#!/usr/bin/env python3
"""
Fix Paper Dates
修复论文日期

Resolves published_date for all entries in papers.json:
- Papers with arXiv ID: query arXiv API for the precise submission date
  (fallback to YYMM-15 if API unavailable)
- Papers with only DOI: query Crossref API for published date
- Papers with neither: keep fallback (YYYY-01-01)

Re-processes entries whose existing published_date ends with "-15" or
"-01-01", as these are approximations from the previous version.

Usage:
    python scripts/fix_dates.py
    python scripts/fix_dates.py --dry-run
"""

import sys
import re
import time
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.db_manager import load_database, save_database
from lib.api_client import ArxivClient, CrossrefClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATABASE_PATH = Path("data/papers.json")


def date_from_arxiv_api(arxiv_client: ArxivClient, arxiv_id: str,
                        max_retries: int = 3) -> Optional[str]:
    """
    Query arXiv API for the precise submission date, with retry on 429.

    Args:
        arxiv_client: ArxivClient instance
        arxiv_id: arXiv identifier (e.g. "2604.09081")
        max_retries: Maximum number of retries on rate-limit errors

    Returns:
        Date string YYYY-MM-DD or None on failure
    """
    for attempt in range(max_retries + 1):
        response = arxiv_client.get_paper(arxiv_id)
        if response.success and response.data:
            published = response.data.get('published')
            if published:
                m = re.match(r'^(\d{4}-\d{2}-\d{2})', published)
                if m:
                    return m.group(1)
            return None

        # Check if this was a 429 rate-limit error
        if response.error and '429' in str(response.error):
            if attempt < max_retries:
                wait = 10 * (2 ** attempt)  # 10s, 20s, 40s
                logger.warning(f"arXiv 429 for {arxiv_id}, retry in {wait}s "
                               f"(attempt {attempt + 1}/{max_retries + 1})")
                time.sleep(wait)
                continue

        # Non-retryable failure
        return None

    logger.warning(f"arXiv API gave up after {max_retries + 1} attempts for {arxiv_id}")
    return None


def date_from_arxiv_id(arxiv_id: str) -> Optional[str]:
    """Fallback: extract approximate date from arXiv ID (YYMM.NNNNN -> YYYY-MM-15)."""
    m = re.match(r'^(\d{2})(\d{2})\.\d+', str(arxiv_id))
    if m:
        yy = int(m.group(1))
        mm = int(m.group(2))
        full_year = 2000 + yy
        if 1 <= mm <= 12:
            return f"{full_year:04d}-{mm:02d}-15"
    return None


def is_approximate_date(date_str: str) -> bool:
    """Check if a date string is an approximation (ends with -15 or -01-01)."""
    if not date_str:
        return True
    s = str(date_str)
    return s.endswith('-15') or s.endswith('-01-01')


def fix_dates(dry_run: bool = False) -> dict:
    """Fix dates for all entries in the database."""
    db = load_database(DATABASE_PATH)
    entries = db.get('entries', [])

    arxiv_client = ArxivClient()
    crossref = CrossrefClient()

    stats = {
        'total': len(entries),
        'already_precise': 0,
        'from_arxiv_api': 0,
        'from_arxiv_id': 0,
        'from_crossref': 0,
        'crossref_failed': 0,
        'no_identifier': 0,
    }

    for i, entry in enumerate(entries):
        entry_id = entry.get('entry_id', '?')
        arxiv_id = entry.get('arxiv_id')
        doi = entry.get('doi')

        existing = entry.get('published_date')
        existing_str = str(existing) if existing else ''

        # Skip if already has a precise (non-approximate) date
        if existing and re.match(r'^\d{4}-\d{2}-\d{2}$', existing_str):
            if not is_approximate_date(existing_str):
                stats['already_precise'] += 1
                continue

        # Priority 1: arXiv API for precise date
        if arxiv_id:
            date = date_from_arxiv_api(arxiv_client, arxiv_id)
            if date:
                if not dry_run:
                    entry['published_date'] = date
                stats['from_arxiv_api'] += 1
                if (i + 1) % 50 == 0:
                    logger.info(f"Progress: {i + 1}/{len(entries)}")
                continue

            # Fallback: approximate from arXiv ID
            date = date_from_arxiv_id(arxiv_id)
            if date:
                # Only use the fallback if we don't already have something
                if not existing or is_approximate_date(existing_str):
                    if not dry_run:
                        entry['published_date'] = date
                    stats['from_arxiv_id'] += 1
                    continue

        # Priority 2: DOI -> Crossref
        if doi:
            try:
                response = crossref.get_paper(doi)
                if response.success and response.data:
                    pub_date = response.data.get('published_date')
                    if pub_date and not pub_date.startswith('None'):
                        if re.match(r'^\d{4}-\d{2}-\d{2}$', pub_date):
                            if not dry_run:
                                entry['published_date'] = pub_date
                            stats['from_crossref'] += 1
                            if (i + 1) % 50 == 0:
                                logger.info(f"Progress: {i + 1}/{len(entries)}")
                            continue
                stats['crossref_failed'] += 1
                logger.debug(f"Crossref failed for {doi}")
            except Exception as e:
                stats['crossref_failed'] += 1
                logger.warning(f"Crossref error for {doi}: {e}")
            continue

        # No identifier available
        stats['no_identifier'] += 1

    # Save
    if not dry_run:
        save_database(db, DATABASE_PATH)

    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Fix paper dates in the database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/fix_dates.py --dry-run
    python scripts/fix_dates.py
        """
    )
    parser.add_argument('--dry-run', action='store_true',
                        help="Show what would be done without making changes")

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("FIX PAPER DATES")
    print("=" * 60 + "\n")

    if args.dry_run:
        print("[DRY RUN] No changes will be made\n")

    stats = fix_dates(dry_run=args.dry_run)

    print("\n" + "-" * 60)
    print("SUMMARY")
    print("-" * 60)
    print(f"Total entries:            {stats['total']}")
    print(f"Already precise:          {stats['already_precise']}")
    print(f"Date from arXiv API:      {stats['from_arxiv_api']}")
    print(f"Date from arXiv ID:       {stats['from_arxiv_id']}")
    print(f"Date from Crossref:       {stats['from_crossref']}")
    print(f"Crossref failed:          {stats['crossref_failed']}")
    print(f"No identifier:            {stats['no_identifier']}")

    if args.dry_run:
        print("\n[DRY RUN] No files were actually written")
    else:
        print(f"\nDone!")


if __name__ == '__main__':
    main()
