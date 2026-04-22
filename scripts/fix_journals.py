#!/usr/bin/env python3
"""
Fix Journal Names
修复期刊名称

Fills the `journal` field for entries in papers.json that are missing it,
by querying the Crossref API (container-title).

Usage:
    python scripts/fix_journals.py --dry-run   # Preview changes
    python scripts/fix_journals.py             # Apply changes
"""

import sys
import html
import argparse
import logging
from pathlib import Path
from collections import Counter

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.db_manager import load_database, save_database
from lib.api_client import CrossrefClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATABASE_PATH = Path("data/papers.json")


def fix_journals(dry_run: bool = False) -> dict:
    """Fill missing journal fields using Crossref API."""
    db = load_database(DATABASE_PATH)
    entries = db.get('entries', [])

    crossref = CrossrefClient()

    stats = {
        'total': len(entries),
        'already_has_journal': 0,
        'no_doi': 0,
        'from_crossref': 0,
        'crossref_empty': 0,
        'crossref_failed': 0,
    }

    # Track all journal names found
    journal_names = Counter()

    for i, entry in enumerate(entries):
        entry_id = entry.get('entry_id', '?')
        doi = entry.get('doi')

        # Skip if already has journal
        existing_journal = entry.get('journal')
        if existing_journal:
            stats['already_has_journal'] += 1
            journal_names[existing_journal] += 1
            continue

        # Need DOI to query Crossref
        if not doi:
            stats['no_doi'] += 1
            continue

        # Query Crossref
        try:
            response = crossref.get_paper(doi)
            if response.success and response.data:
                journal = response.data.get('journal', '')
                if journal and journal.strip():
                    journal = html.unescape(journal.strip())
                    if not dry_run:
                        entry['journal'] = journal
                    stats['from_crossref'] += 1
                    journal_names[journal] += 1
                    if (i + 1) % 100 == 0:
                        logger.info(f"Progress: {i + 1}/{len(entries)}")
                    continue
                else:
                    stats['crossref_empty'] += 1
                    logger.debug(f"Crossref returned empty journal for {doi}")
            else:
                stats['crossref_failed'] += 1
                logger.debug(f"Crossref failed for {doi}")
        except Exception as e:
            stats['crossref_failed'] += 1
            logger.warning(f"Crossref error for {doi}: {e}")

    # Save
    if not dry_run:
        save_database(db, DATABASE_PATH)

    return stats, journal_names


def main():
    parser = argparse.ArgumentParser(
        description='Fix missing journal names in the database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/fix_journals.py --dry-run
    python scripts/fix_journals.py
        """
    )
    parser.add_argument('--dry-run', action='store_true',
                        help="Show what would be done without making changes")

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("FIX JOURNAL NAMES")
    print("=" * 60 + "\n")

    if args.dry_run:
        print("[DRY RUN] No changes will be made\n")

    stats, journal_names = fix_journals(dry_run=args.dry_run)

    print("\n" + "-" * 60)
    print("SUMMARY")
    print("-" * 60)
    print(f"Total entries:           {stats['total']}")
    print(f"Already had journal:     {stats['already_has_journal']}")
    print(f"Filled from Crossref:    {stats['from_crossref']}")
    print(f"Crossref empty journal:  {stats['crossref_empty']}")
    print(f"Crossref failed:         {stats['crossref_failed']}")
    print(f"No DOI (skipped):        {stats['no_doi']}")

    # Import the abbreviation table to check for unmapped journals
    try:
        from sync_database import JOURNAL_NAME_ABBREV
    except ImportError:
        JOURNAL_NAME_ABBREV = {}

    # Show unmapped journals (sorted by frequency)
    unmapped = []
    for name, count in journal_names.most_common():
        if name not in JOURNAL_NAME_ABBREV:
            # Also check case-insensitive
            found = False
            for known in JOURNAL_NAME_ABBREV:
                if known.lower() == name.lower():
                    found = True
                    break
            if not found:
                unmapped.append((name, count))

    if unmapped:
        print(f"\n" + "-" * 60)
        print(f"UNMAPPED JOURNALS ({len(unmapped)} unique)")
        print("-" * 60)
        for name, count in unmapped[:50]:
            print(f"  {count:3d}x  {name}")
        if len(unmapped) > 50:
            print(f"  ... and {len(unmapped) - 50} more")

    if args.dry_run:
        print("\n[DRY RUN] No files were actually written")
    else:
        print(f"\nDone!")


if __name__ == '__main__':
    main()
