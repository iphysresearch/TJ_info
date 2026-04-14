#!/usr/bin/env python3
"""
Update Citation Counts for All Papers
更新所有论文的引用计数

This script fetches fresh citation counts from Semantic Scholar
for all papers in the database.

Usage:
    python scripts/update_citations.py
    python scripts/update_citations.py --dry-run
"""

import sys
import json
import argparse
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.api_client import SemanticScholarClient
from lib.db_manager import load_database, save_database, update_entry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
DATABASE_PATH = Path("data/papers.json")


def update_citation_count(entry: Dict[str, Any],
                          s2_client: SemanticScholarClient) -> Dict[str, Any]:
    """
    Update citation count for a single entry.

    Args:
        entry: Paper entry dictionary
        s2_client: Semantic Scholar client

    Returns:
        Updated citations dictionary
    """
    arxiv_id = entry.get('arxiv_id')
    doi = entry.get('doi')

    response = None
    if arxiv_id:
        response = s2_client.get_paper(arxiv_id, id_type='arxiv')
    elif doi:
        response = s2_client.get_paper(doi, id_type='doi')

    if response and response.success:
        return {
            'count': response.data.get('citation_count', 0),
            'last_updated': datetime.now().strftime('%Y-%m-%d'),
            'source': 'semantic_scholar'
        }

    # Keep existing data if fetch failed
    return entry.get('citations', {
        'count': 0,
        'last_updated': datetime.now().strftime('%Y-%m-%d'),
        'source': 'manual'
    })


def main():
    parser = argparse.ArgumentParser(
        description='Update citation counts for all papers',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--dry-run', action='store_true',
                        help="Show what would be done without making changes")
    parser.add_argument('--delay', type=float, default=1.0,
                        help="Delay between API requests in seconds (default: 1.0)")

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("UPDATE CITATION COUNTS")
    print("=" * 60 + "\n")

    # Load database
    db = load_database(DATABASE_PATH)
    entries = db.get('entries', [])

    print(f"Found {len(entries)} entries to update\n")

    if args.dry_run:
        print("[DRY RUN] No changes will be made\n")

    # Initialize client
    s2_client = SemanticScholarClient()

    updated_count = 0
    failed_count = 0
    total_citations = 0

    for i, entry in enumerate(entries, 1):
        entry_id = entry.get('entry_id', 'unknown')
        title = entry.get('title', 'Unknown')[:50]

        print(f"[{i}/{len(entries)}] {title}...")

        if not args.dry_run:
            old_count = entry.get('citations', {}).get('count', 0)
            new_citations = update_citation_count(entry, s2_client)
            new_count = new_citations.get('count', 0)

            if new_citations.get('source') == 'semantic_scholar':
                entry['citations'] = new_citations
                change = new_count - old_count
                change_str = f"+{change}" if change > 0 else str(change)
                print(f"    Citations: {old_count} → {new_count} ({change_str})")
                updated_count += 1
                total_citations += new_count
            else:
                print(f"    Failed to fetch (keeping existing: {old_count})")
                failed_count += 1
                total_citations += old_count

            # Rate limiting
            if i < len(entries):
                time.sleep(args.delay)
        else:
            print(f"    [DRY RUN] Would update citations")
            updated_count += 1

    # Save database
    if not args.dry_run and updated_count > 0:
        save_database(db, DATABASE_PATH)

    # Summary
    print("\n" + "─" * 60)
    print("SUMMARY")
    print("─" * 60)
    print(f"Total entries: {len(entries)}")
    print(f"Successfully updated: {updated_count}")
    print(f"Failed: {failed_count}")

    if not args.dry_run:
        print(f"Total citations: {total_citations}")
        print(f"\n✅ Database saved")
    else:
        print("\n[DRY RUN] No changes were made")


if __name__ == '__main__':
    main()
