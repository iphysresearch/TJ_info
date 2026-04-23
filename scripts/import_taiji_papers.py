#!/usr/bin/env python3
"""
Import Taiji Collaboration Papers from Excel
从 Excel 导入太极联盟论文

This script reads papers from an Excel file and imports them into the database,
marking them as official Taiji Collaboration publications.

Usage:
    python scripts/import_taiji_papers.py --input 123123.xlsx
    python scripts/import_taiji_papers.py --input 123123.xlsx --dry-run
"""

import sys
import json
import argparse
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Set, Optional

import pandas as pd

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.api_client import CrossrefClient
from lib.db_manager import load_database, save_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
DATABASE_PATH = Path("data/papers.json")


def normalize_doi(doi: str) -> str:
    """Normalize DOI to lowercase for comparison."""
    if not doi:
        return ""
    return doi.strip().lower()


def get_existing_dois(db: Dict[str, Any]) -> Set[str]:
    """Get set of DOIs already in database (normalized)."""
    dois = set()
    for entry in db.get('entries', []):
        if entry.get('doi'):
            dois.add(normalize_doi(entry['doi']))
    return dois


def read_excel_dois(filepath: str, sheets: List[str] = ['A', 'B', 'C']) -> List[str]:
    """
    Read DOIs from specified sheets in Excel file.

    Args:
        filepath: Path to Excel file
        sheets: List of sheet names to read

    Returns:
        List of unique DOIs
    """
    all_dois = []
    xl = pd.ExcelFile(filepath)

    for sheet in sheets:
        if sheet not in xl.sheet_names:
            logger.warning(f"Sheet '{sheet}' not found in Excel file")
            continue

        df = pd.read_excel(xl, sheet_name=sheet)

        if 'DOI号' not in df.columns:
            logger.warning(f"Sheet '{sheet}' has no 'DOI号' column")
            continue

        dois = df['DOI号'].dropna().tolist()
        all_dois.extend([str(d).strip() for d in dois if str(d).strip()])
        logger.info(f"Sheet {sheet}: {len(dois)} DOIs")

    # Remove duplicates while preserving order
    seen = set()
    unique_dois = []
    for doi in all_dois:
        normalized = normalize_doi(doi)
        if normalized not in seen:
            seen.add(normalized)
            unique_dois.append(doi)

    logger.info(f"Total unique DOIs: {len(unique_dois)}")
    return unique_dois


def create_entry_from_crossref(data: Dict[str, Any], doi: str) -> Dict[str, Any]:
    """
    Create a database entry from Crossref API response.

    Args:
        data: Crossref API response data
        doi: Original DOI string

    Returns:
        Database entry dictionary
    """
    # Build authors list
    authors = []
    for author in data.get('authors', []):
        authors.append({
            'name': author.get('name', ''),
            'affiliation': author.get('affiliation')
        })

    entry = {
        'entry_id': doi,
        'title': data.get('title', ''),
        'authors': authors,
        'year': data.get('year'),
        'journal': data.get('journal', ''),
        'doi': doi,
        'arxiv_id': None,
        'keywords': data.get('subject', []),
        'publication_type': 'journal',
        'featured': False,
        'citation_count': data.get('is_referenced_by_count', 0),
        'classification': {
            'research_area': None,
            'source_types': [],
            'methods': [],
            'relevance_score': 1.0
        },
        'published_date': data.get('published_date'),
        'taiji_collaboration': True
    }

    # Add volume/pages if available
    if data.get('volume'):
        entry['volume'] = data['volume']
    if data.get('pages'):
        entry['pages'] = data['pages']

    return entry


def import_taiji_papers(
    input_file: str,
    sheets: List[str] = ['A', 'B', 'C'],
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Import Taiji Collaboration papers from Excel file.

    Args:
        input_file: Path to Excel file
        sheets: List of sheet names to process
        dry_run: If True, don't save changes

    Returns:
        Statistics dictionary
    """
    stats = {
        'total_dois': 0,
        'already_in_db': 0,
        'marked_existing': 0,
        'added_new': 0,
        'failed': 0,
        'failed_dois': []
    }

    # Read DOIs from Excel
    dois = read_excel_dois(input_file, sheets)
    stats['total_dois'] = len(dois)

    # Load database
    db = load_database(DATABASE_PATH)
    existing_dois = get_existing_dois(db)

    # Initialize Crossref client
    crossref = CrossrefClient()

    # Process each DOI
    for i, doi in enumerate(dois):
        normalized = normalize_doi(doi)

        if normalized in existing_dois:
            # Paper already in database - just mark it
            stats['already_in_db'] += 1

            # Find and update the entry
            for entry in db['entries']:
                if normalize_doi(entry.get('doi', '')) == normalized:
                    if not entry.get('taiji_collaboration'):
                        entry['taiji_collaboration'] = True
                        stats['marked_existing'] += 1
                        logger.info(f"[{i+1}/{len(dois)}] Marked existing: {doi}")
                    else:
                        logger.debug(f"[{i+1}/{len(dois)}] Already marked: {doi}")
                    break
        else:
            # New paper - fetch from Crossref
            logger.info(f"[{i+1}/{len(dois)}] Fetching: {doi}")

            response = crossref.get_paper(doi)

            if response.success and response.data:
                entry = create_entry_from_crossref(response.data, doi)
                db['entries'].append(entry)
                existing_dois.add(normalized)
                stats['added_new'] += 1
                logger.info(f"  Added: {entry['title'][:60]}...")
            else:
                stats['failed'] += 1
                stats['failed_dois'].append(doi)
                logger.warning(f"  Failed: {response.error}")

            # Rate limiting - be nice to Crossref
            time.sleep(0.5)

    # Update metadata
    db['metadata']['total_entries'] = len(db['entries'])
    db['metadata']['last_updated'] = pd.Timestamp.now().strftime('%Y-%m-%d')

    # Save database
    if not dry_run:
        save_database(db, DATABASE_PATH)
        logger.info(f"Database saved to {DATABASE_PATH}")
    else:
        logger.info("[DRY RUN] Database not saved")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Import Taiji Collaboration papers from Excel file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/import_taiji_papers.py --input 123123.xlsx
    python scripts/import_taiji_papers.py --input 123123.xlsx --dry-run
    python scripts/import_taiji_papers.py --input 123123.xlsx --sheets A B
        """
    )

    parser.add_argument('--input', '-i', required=True,
                        help="Path to Excel file")
    parser.add_argument('--sheets', '-s', nargs='+', default=['A', 'B', 'C'],
                        help="Sheet names to process (default: A B C)")
    parser.add_argument('--dry-run', action='store_true',
                        help="Show what would be done without making changes")

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("IMPORT TAIJI COLLABORATION PAPERS")
    print("=" * 60 + "\n")

    print(f"Input file: {args.input}")
    print(f"Sheets: {args.sheets}")
    print(f"Dry run: {args.dry_run}")
    print()

    stats = import_taiji_papers(
        input_file=args.input,
        sheets=args.sheets,
        dry_run=args.dry_run
    )

    print("\n" + "─" * 60)
    print("SUMMARY")
    print("─" * 60)
    print(f"Total DOIs in Excel: {stats['total_dois']}")
    print(f"Already in database: {stats['already_in_db']}")
    print(f"  - Newly marked as Taiji: {stats['marked_existing']}")
    print(f"Added new papers: {stats['added_new']}")
    print(f"Failed to fetch: {stats['failed']}")

    if stats['failed_dois']:
        print("\nFailed DOIs:")
        for doi in stats['failed_dois']:
            print(f"  - {doi}")

    if args.dry_run:
        print("\n[DRY RUN] No changes were saved")
    else:
        print(f"\n✅ Import complete!")

    return 0 if stats['failed'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
