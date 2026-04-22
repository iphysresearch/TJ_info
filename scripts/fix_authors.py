#!/usr/bin/env python3
"""
Fix Abbreviated Author Names
修复缩写作者姓名

Expands abbreviated author names (e.g., "Q. Liang" → "Qian Liang") by
querying arXiv, Crossref, and INSPIRE APIs for full author lists.

Usage:
    python scripts/fix_authors.py
    python scripts/fix_authors.py --dry-run
    python scripts/fix_authors.py --dry-run --limit 10
"""

import sys
import re
import argparse
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.db_manager import load_database, save_database
from lib.api_client import ArxivClient, CrossrefClient, InspireClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATABASE_PATH = Path("data/papers.json")


def strip_cjk(s: str) -> str:
    """Remove CJK characters and fullwidth punctuation, collapse spaces."""
    cleaned = re.sub(r'[\u4e00-\u9fff\u3400-\u4dbf\u3000-\u303f\uff00-\uffef]+', '', s)
    return re.sub(r'\s+', ' ', cleaned).strip()


def is_abbreviated(name: str) -> bool:
    """
    Check if a name is abbreviated.

    Abbreviated means the first token matches ^[A-Z]\.$ (single uppercase letter + dot).
    Excludes names like "Li-E. Qiang" or "Soumya D. Mohanty" where an abbreviated
    token appears after the first non-abbreviated token.

    Examples:
        "Q. Liang" → True
        "S. R. Valluri" → True
        "Qian Liang" → False
        "Li-E. Qiang" → False
        "Soumya D. Mohanty" → False
    """
    if not name or not name.strip():
        return False

    tokens = name.strip().split()
    if len(tokens) < 2:
        return False

    first = tokens[0]
    return bool(re.match(r'^[A-Z]\.$', first))


def extract_surname(name: str) -> str:
    """Extract the surname (last token) from a CJK-cleaned name."""
    cleaned = strip_cjk(name)
    tokens = cleaned.split()
    return tokens[-1] if tokens else ""


def extract_initials(name: str) -> List[str]:
    """
    Extract initials from a CJK-cleaned name.

    "Q. Liang" → ["Q"]
    "S. R. Valluri" → ["S", "R"]
    "Qian Liang" → ["Q"]
    "Shao-Jiang Wang" → ["S"]
    "Liang-Gui 良贵 Zhu 朱" → ["L"]
    """
    cleaned = strip_cjk(name)
    tokens = cleaned.split()
    initials = []
    for t in tokens[:-1]:  # Exclude surname
        if re.match(r'^[A-Z]\.$', t):
            initials.append(t[0])
        elif t and t[0].isalpha():
            initials.append(t[0].upper())
    return initials


def names_match(abbreviated: str, full: str) -> bool:
    """
    Check if an abbreviated name matches a full name.

    Matching criteria:
    1. Same surname (case-insensitive)
    2. Initials of abbreviated name match initials of full name
    """
    surname_abbr = extract_surname(abbreviated).lower()
    surname_full = extract_surname(full).lower()

    if surname_abbr != surname_full:
        return False

    initials_abbr = extract_initials(abbreviated)
    initials_full = extract_initials(full)

    if not initials_abbr:
        return False

    # Check that each abbreviated initial matches the corresponding full initial
    # Allow the full name to have more initials than the abbreviated one
    for i, init in enumerate(initials_abbr):
        if i >= len(initials_full):
            return False
        if init.upper() != initials_full[i].upper():
            return False

    return True


def fetch_authors_from_apis(entry: Dict[str, Any],
                            arxiv_client: ArxivClient,
                            crossref_client: CrossrefClient,
                            inspire_client: InspireClient) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch full author list from APIs, trying in priority order:
    1. Crossref (no hard rate limit, has given + family)
    2. arXiv (has full names but strict rate limit)
    3. INSPIRE-HEP (has full_name)
    """
    arxiv_id = entry.get('arxiv_id')
    doi = entry.get('doi')

    # Try Crossref first (no hard rate limit)
    if doi:
        try:
            response = crossref_client.get_paper(doi)
            if response.success and response.data:
                authors = response.data.get('authors', [])
                # Check that Crossref returned non-abbreviated names
                if authors and any(
                    a.get('name') and not is_abbreviated(a['name'])
                    for a in authors
                ):
                    return authors
        except Exception as e:
            logger.debug(f"Crossref error for {doi}: {e}")

    # Try arXiv (stricter rate limit)
    if arxiv_id:
        try:
            response = arxiv_client.get_paper(arxiv_id)
            if response.success and response.data:
                authors = response.data.get('authors', [])
                if authors and any(a.get('name') for a in authors):
                    return authors
        except Exception as e:
            logger.debug(f"arXiv error for {arxiv_id}: {e}")

    # Try INSPIRE
    if arxiv_id:
        try:
            response = inspire_client.get_paper(arxiv_id, id_type='arxiv')
            if response.success and response.data:
                authors = response.data.get('authors', [])
                if authors and any(a.get('name') for a in authors):
                    return authors
        except Exception as e:
            logger.debug(f"INSPIRE error for {arxiv_id}: {e}")
    elif doi:
        try:
            response = inspire_client.get_paper(doi, id_type='doi')
            if response.success and response.data:
                authors = response.data.get('authors', [])
                if authors and any(a.get('name') for a in authors):
                    return authors
        except Exception as e:
            logger.debug(f"INSPIRE error for {doi}: {e}")

    return None


def fix_authors(dry_run: bool = False, limit: int = 0) -> dict:
    """Fix abbreviated author names in the database."""
    db = load_database(DATABASE_PATH)
    entries = db.get('entries', [])

    arxiv_client = ArxivClient()
    crossref_client = CrossrefClient()
    inspire_client = InspireClient()

    stats = {
        'total': len(entries),
        'entries_with_abbrev': 0,
        'entries_fixed': 0,
        'entries_partial': 0,
        'entries_no_api_data': 0,
        'names_replaced': 0,
        'names_not_matched': 0,
    }

    # Find entries with abbreviated names
    entries_to_fix = []
    for entry in entries:
        authors = entry.get('authors', [])
        has_abbrev = any(is_abbreviated(a.get('name', '')) for a in authors)
        if has_abbrev:
            entries_to_fix.append(entry)

    stats['entries_with_abbrev'] = len(entries_to_fix)
    logger.info(f"Found {len(entries_to_fix)} entries with abbreviated names")

    if limit > 0:
        entries_to_fix = entries_to_fix[:limit]
        logger.info(f"Limited to {limit} entries")

    for i, entry in enumerate(entries_to_fix):
        entry_id = entry.get('entry_id', '?')

        if (i + 1) % 50 == 0:
            logger.info(f"Progress: {i + 1}/{len(entries_to_fix)}")

        # Fetch full author list from APIs
        api_authors = fetch_authors_from_apis(
            entry, arxiv_client, crossref_client, inspire_client
        )

        if not api_authors:
            stats['entries_no_api_data'] += 1
            continue

        # Build lookup: surname → list of full names from API (CJK-cleaned)
        api_by_surname: Dict[str, List[str]] = {}
        for a in api_authors:
            name = a.get('name', '')
            if not name:
                continue
            cleaned = strip_cjk(name)
            if not cleaned:
                continue
            surname = extract_surname(cleaned).lower()
            if surname not in api_by_surname:
                api_by_surname[surname] = []
            api_by_surname[surname].append(cleaned)

        # Try to replace each abbreviated name
        entry_replaced = 0
        entry_not_matched = 0
        current_authors = entry.get('authors', [])

        for author in current_authors:
            name = author.get('name', '')
            if not is_abbreviated(name):
                continue

            surname = extract_surname(strip_cjk(name)).lower()
            candidates = api_by_surname.get(surname, [])

            matched = False
            for candidate in candidates:
                if not is_abbreviated(candidate) and names_match(name, candidate):
                    if not dry_run:
                        author['name'] = candidate
                    entry_replaced += 1
                    matched = True
                    break

            if not matched:
                entry_not_matched += 1

        stats['names_replaced'] += entry_replaced
        stats['names_not_matched'] += entry_not_matched

        if entry_replaced > 0 and entry_not_matched == 0:
            stats['entries_fixed'] += 1
        elif entry_replaced > 0:
            stats['entries_partial'] += 1

    # Save
    if not dry_run:
        save_database(db, DATABASE_PATH)

    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Fix abbreviated author names in the database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/fix_authors.py --dry-run --limit 10
    python scripts/fix_authors.py --dry-run
    python scripts/fix_authors.py
        """
    )
    parser.add_argument('--dry-run', action='store_true',
                        help="Show what would be done without making changes")
    parser.add_argument('--limit', type=int, default=0,
                        help="Limit the number of entries to process (0 = all)")

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("FIX ABBREVIATED AUTHOR NAMES")
    print("=" * 60 + "\n")

    if args.dry_run:
        print("[DRY RUN] No changes will be made\n")

    stats = fix_authors(dry_run=args.dry_run, limit=args.limit)

    print("\n" + "-" * 60)
    print("SUMMARY")
    print("-" * 60)
    print(f"Total entries:                {stats['total']}")
    print(f"Entries with abbreviations:   {stats['entries_with_abbrev']}")
    print(f"Entries fully fixed:          {stats['entries_fixed']}")
    print(f"Entries partially fixed:      {stats['entries_partial']}")
    print(f"Entries no API data:          {stats['entries_no_api_data']}")
    print(f"Names replaced:               {stats['names_replaced']}")
    print(f"Names not matched:            {stats['names_not_matched']}")

    if args.dry_run:
        print("\n[DRY RUN] No files were actually written")
    else:
        print(f"\nDone!")


if __name__ == '__main__':
    main()
