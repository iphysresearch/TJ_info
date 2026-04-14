#!/usr/bin/env python3
"""
Sync Database to Hugo Content
同步数据库到 Hugo 内容

This script synchronizes the papers.json database to Hugo markdown files
and data files.

Usage:
    python scripts/sync_database.py
    python scripts/sync_database.py --dry-run
"""

import sys
import json
import argparse
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.db_manager import load_database, get_all_entries

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
DATABASE_PATH = Path("data/papers.json")
HUGO_CONTENT_PATH = Path("content/publications")
HUGO_DATA_PATH = Path("data")


def generate_frontmatter(entry: Dict[str, Any]) -> str:
    """
    Generate Hugo frontmatter YAML from entry.

    Args:
        entry: Paper entry dictionary

    Returns:
        YAML frontmatter string
    """
    lines = ['---']

    # Title (escape quotes)
    title = entry.get('title', '').replace('"', '\\"')
    lines.append(f'title: "{title}"')

    # Date (use publication date or fallback to added date)
    year = entry.get('year', datetime.now().year)
    added_date = entry.get('metadata', {}).get('added_date', datetime.now().strftime('%Y-%m-%d'))

    # Create a date in the publication year
    if added_date.startswith(str(year)):
        date = added_date
    else:
        date = f"{year}-01-01"
    lines.append(f'date: {date}')

    # Authors
    lines.append('authors:')
    for author in entry.get('authors', []):
        lines.append(f'  - name: "{author.get("name", "")}"')
        if author.get('affiliation'):
            lines.append(f'    affiliation: "{author["affiliation"]}"')

    # Journal info
    if entry.get('journal'):
        lines.append(f'journal: "{entry["journal"]}"')
    if entry.get('volume'):
        lines.append(f'volume: "{entry["volume"]}"')
    if entry.get('pages'):
        lines.append(f'pages: "{entry["pages"]}"')

    # Year
    lines.append(f'year: {year}')

    # Identifiers
    if entry.get('arxiv_id'):
        lines.append(f'arxiv: "{entry["arxiv_id"]}"')
    if entry.get('doi'):
        lines.append(f'doi: "{entry["doi"]}"')

    # Keywords
    if entry.get('keywords'):
        lines.append('keywords:')
        for kw in entry['keywords']:
            lines.append(f'  - "{kw}"')

    # Abstract
    if entry.get('abstract'):
        abstract = entry['abstract'].replace('\n', '\n  ')
        lines.append('abstract: |')
        lines.append(f'  {abstract}')

    # Publication type
    pub_type = entry.get('publication_type', 'journal')
    lines.append(f'publication_type: "{pub_type}"')

    # Featured
    featured = entry.get('featured', False)
    lines.append(f'featured: {str(featured).lower()}')

    # Citation count (if available)
    citations = entry.get('citations', {})
    if citations.get('count', 0) > 0:
        lines.append(f'citation_count: {citations["count"]}')

    lines.append('---')

    return '\n'.join(lines)


def generate_content(entry: Dict[str, Any]) -> str:
    """
    Generate Hugo content body from entry.

    Args:
        entry: Paper entry dictionary

    Returns:
        Markdown content string
    """
    lines = []

    # Summary from abstract (first 200 chars)
    abstract = entry.get('abstract', '')
    if abstract:
        summary = abstract[:200].rsplit(' ', 1)[0] + '...' if len(abstract) > 200 else abstract
        lines.append(summary)

    return '\n'.join(lines)


def generate_filename(entry: Dict[str, Any]) -> str:
    """
    Generate filename for Hugo content file.

    Args:
        entry: Paper entry dictionary

    Returns:
        Filename string (without extension)
    """
    year = entry.get('year', datetime.now().year)
    added_date = entry.get('metadata', {}).get('added_date', datetime.now().strftime('%Y-%m-%d'))

    # Use added_date if in the same year, otherwise construct from year
    if added_date.startswith(str(year)):
        date_prefix = added_date
    else:
        date_prefix = f"{year}-01-01"

    # Generate slug from title
    title = entry.get('title', 'untitled')
    slug = title.lower()
    # Remove special characters
    slug = ''.join(c if c.isalnum() or c in ' -' else '' for c in slug)
    # Replace spaces with hyphens
    slug = '-'.join(slug.split())
    # Limit length
    slug = slug[:50].rstrip('-')

    return f"{date_prefix}-{slug}"


def sync_entry_to_hugo(entry: Dict[str, Any], output_dir: Path,
                       dry_run: bool = False) -> tuple[bool, str]:
    """
    Sync a single entry to Hugo content.

    Args:
        entry: Paper entry dictionary
        output_dir: Directory for Hugo content
        dry_run: If True, don't write files

    Returns:
        Tuple of (success, filename)
    """
    filename = generate_filename(entry)
    filepath = output_dir / f"{filename}.md"

    frontmatter = generate_frontmatter(entry)
    content = generate_content(entry)

    full_content = f"{frontmatter}\n\n{content}\n"

    if dry_run:
        logger.info(f"[DRY RUN] Would write: {filepath}")
        return True, filename

    try:
        filepath.write_text(full_content, encoding='utf-8')
        logger.info(f"Wrote: {filepath}")
        return True, filename
    except Exception as e:
        logger.error(f"Failed to write {filepath}: {e}")
        return False, filename


def sync_database_to_hugo(dry_run: bool = False,
                          clean: bool = False) -> Dict[str, Any]:
    """
    Sync entire database to Hugo content directory.

    Args:
        dry_run: If True, don't write files
        clean: If True, remove existing publication files first

    Returns:
        Summary dictionary
    """
    # Load database
    db = load_database(DATABASE_PATH)
    entries = get_all_entries(db)

    logger.info(f"Syncing {len(entries)} entries to Hugo content")

    # Ensure output directory exists
    HUGO_CONTENT_PATH.mkdir(parents=True, exist_ok=True)

    # Clean existing files if requested
    if clean and not dry_run:
        existing_files = list(HUGO_CONTENT_PATH.glob('*.md'))
        # Keep _index.md
        existing_files = [f for f in existing_files if f.name != '_index.md']
        for f in existing_files:
            f.unlink()
            logger.info(f"Removed: {f}")

    # Sync entries
    success_count = 0
    failed_count = 0
    filenames = []

    for entry in entries:
        success, filename = sync_entry_to_hugo(entry, HUGO_CONTENT_PATH, dry_run)
        if success:
            success_count += 1
            filenames.append(filename)
        else:
            failed_count += 1

    # Also update Hugo data file
    if not dry_run:
        hugo_data_file = HUGO_DATA_PATH / "papers.json"
        hugo_data_file.parent.mkdir(parents=True, exist_ok=True)

        # Create a simplified version for Hugo
        hugo_data = {
            'metadata': db.get('metadata', {}),
            'entries': [{
                'entry_id': e.get('entry_id'),
                'title': e.get('title'),
                'authors': e.get('authors', []),
                'year': e.get('year'),
                'journal': e.get('journal'),
                'doi': e.get('doi'),
                'arxiv_id': e.get('arxiv_id'),
                'keywords': e.get('keywords', []),
                'publication_type': e.get('publication_type'),
                'featured': e.get('featured', False),
                'citation_count': e.get('citations', {}).get('count', 0),
                'classification': e.get('classification', {})
            } for e in entries]
        }

        hugo_data_file.write_text(
            json.dumps(hugo_data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        logger.info(f"Updated Hugo data file: {hugo_data_file}")

    return {
        'total': len(entries),
        'success': success_count,
        'failed': failed_count,
        'files': filenames,
        'dry_run': dry_run
    }


def main():
    parser = argparse.ArgumentParser(
        description='Sync database to Hugo content',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/sync_database.py
    python scripts/sync_database.py --dry-run
    python scripts/sync_database.py --clean
        """
    )

    parser.add_argument('--dry-run', action='store_true',
                        help="Show what would be done without making changes")
    parser.add_argument('--clean', action='store_true',
                        help="Remove existing publication files before sync")

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("SYNC DATABASE TO HUGO CONTENT")
    print("=" * 60 + "\n")

    result = sync_database_to_hugo(dry_run=args.dry_run, clean=args.clean)

    print("\n" + "─" * 60)
    print("SUMMARY")
    print("─" * 60)
    print(f"Total entries: {result['total']}")
    print(f"Successfully synced: {result['success']}")
    print(f"Failed: {result['failed']}")

    if result['dry_run']:
        print("\n[DRY RUN] No files were actually written")
    else:
        print(f"\n✅ Sync complete!")

    sys.exit(0 if result['failed'] == 0 else 1)


if __name__ == '__main__':
    main()
