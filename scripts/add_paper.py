#!/usr/bin/env python3
"""
Add Paper to Taiji Publications Database
添加论文到太极出版物数据库

Usage:
    python scripts/add_paper.py --doi 10.1103/PhysRevD.100.022003
    python scripts/add_paper.py --arxiv 2401.12345
    python scripts/add_paper.py --interactive
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.api_client import PaperFetcher, ArxivClient, CrossrefClient, SemanticScholarClient
from lib.db_manager import (
    load_database, save_database, add_entry, find_by_doi, find_by_arxiv,
    generate_entry_id
)
from lib.classifier import classify_paper, suggest_classification
from lib.validator import validate_entry, generate_validation_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
DATABASE_PATH = Path("data/papers.json")
TAXONOMY_PATH = Path("config/taxonomy.yaml")


def fetch_paper_metadata(doi: Optional[str] = None,
                         arxiv_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch paper metadata from external APIs.

    Args:
        doi: Digital Object Identifier
        arxiv_id: arXiv identifier

    Returns:
        Paper metadata dictionary or None if not found
    """
    fetcher = PaperFetcher()

    if arxiv_id:
        logger.info(f"Fetching metadata for arXiv:{arxiv_id}")
        data = fetcher.fetch_by_arxiv(arxiv_id)
        if not data.get('title'):
            logger.error(f"Could not fetch paper: arXiv:{arxiv_id}")
            return None
        return data

    elif doi:
        logger.info(f"Fetching metadata for DOI:{doi}")
        data = fetcher.fetch_by_doi(doi)
        if not data.get('title'):
            logger.error(f"Could not fetch paper: DOI:{doi}")
            return None
        return data

    return None


def create_entry_from_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a database entry from fetched metadata.

    Args:
        metadata: Raw metadata from API

    Returns:
        Formatted entry dictionary
    """
    # Generate entry ID
    entry_id = generate_entry_id(
        doi=metadata.get('doi'),
        arxiv_id=metadata.get('arxiv_id'),
        title=metadata.get('title'),
        year=metadata.get('year')
    )

    # Parse year from date if needed
    year = metadata.get('year')
    if not year and metadata.get('published'):
        try:
            year = int(metadata['published'][:4])
        except (ValueError, TypeError):
            year = datetime.now().year

    # Format authors
    authors = []
    for author in metadata.get('authors', []):
        if isinstance(author, dict):
            authors.append({
                'name': author.get('name', ''),
                'affiliation': author.get('affiliation')
            })
        elif isinstance(author, str):
            authors.append({'name': author})

    # Extract keywords from categories or subject
    keywords = metadata.get('keywords', [])
    if not keywords and metadata.get('categories'):
        keywords = metadata['categories'][:5]  # Limit to 5 categories
    if not keywords and metadata.get('subject'):
        keywords = metadata['subject'][:5]

    # Create entry
    entry = {
        'entry_id': entry_id,
        'title': metadata.get('title', '').strip(),
        'authors': authors,
        'year': year,
        'journal': metadata.get('journal'),
        'volume': metadata.get('volume'),
        'pages': metadata.get('pages'),
        'doi': metadata.get('doi'),
        'arxiv_id': metadata.get('arxiv_id'),
        'url': metadata.get('url'),
        'abstract': metadata.get('abstract', '').strip() if metadata.get('abstract') else None,
        'keywords': keywords,
        'publication_type': 'preprint' if metadata.get('arxiv_id') and not metadata.get('journal') else 'journal',
        'featured': False,
        'citations': {
            'count': metadata.get('citation_count', 0),
            'last_updated': datetime.now().strftime('%Y-%m-%d'),
            'source': 'semantic_scholar' if metadata.get('citation_count') else 'manual'
        },
        'metadata': {
            'added_date': datetime.now().strftime('%Y-%m-%d'),
            'last_updated': datetime.now().strftime('%Y-%m-%d'),
            'data_sources': metadata.get('data_sources', []),
            'quality_score': 1.0,
            'review_status': 'pending'
        }
    }

    # Auto-classify
    classification = classify_paper(entry, TAXONOMY_PATH)
    entry['classification'] = classification

    # Remove None values
    entry = {k: v for k, v in entry.items() if v is not None}

    return entry


def interactive_add():
    """Interactive mode for adding papers."""
    print("\n" + "=" * 60)
    print("Add Paper to Taiji Publications Database")
    print("添加论文到太极出版物数据库")
    print("=" * 60 + "\n")

    # Get identifier
    print("How would you like to add the paper?")
    print("  1. By DOI")
    print("  2. By arXiv ID")
    print("  3. Manual entry")
    print()

    choice = input("Enter choice (1/2/3): ").strip()

    if choice == '1':
        doi = input("Enter DOI (e.g., 10.1103/PhysRevD.100.022003): ").strip()
        if not doi:
            print("No DOI provided. Exiting.")
            return False
        return add_paper(doi=doi, interactive=True)

    elif choice == '2':
        arxiv_id = input("Enter arXiv ID (e.g., 2401.12345): ").strip()
        if not arxiv_id:
            print("No arXiv ID provided. Exiting.")
            return False
        return add_paper(arxiv_id=arxiv_id, interactive=True)

    elif choice == '3':
        return manual_entry()

    else:
        print("Invalid choice. Exiting.")
        return False


def manual_entry() -> bool:
    """Manually enter paper details."""
    print("\n--- Manual Entry ---\n")

    title = input("Title: ").strip()
    if not title:
        print("Title is required. Exiting.")
        return False

    # Authors
    authors = []
    print("Enter authors (one per line, empty line to finish):")
    while True:
        name = input("  Author name: ").strip()
        if not name:
            break
        affiliation = input("  Affiliation (optional): ").strip()
        authors.append({'name': name, 'affiliation': affiliation or None})

    if not authors:
        print("At least one author is required. Exiting.")
        return False

    year = input("Year: ").strip()
    try:
        year = int(year)
    except ValueError:
        print("Invalid year. Using current year.")
        year = datetime.now().year

    journal = input("Journal (optional): ").strip() or None
    doi = input("DOI (optional): ").strip() or None
    arxiv_id = input("arXiv ID (optional): ").strip() or None

    keywords = input("Keywords (comma-separated): ").strip()
    keywords = [k.strip() for k in keywords.split(',') if k.strip()]

    abstract = input("Abstract (optional, press Enter to skip): ").strip() or None

    # Create entry
    entry = {
        'entry_id': generate_entry_id(doi=doi, arxiv_id=arxiv_id, title=title, year=year),
        'title': title,
        'authors': authors,
        'year': year,
        'journal': journal,
        'doi': doi,
        'arxiv_id': arxiv_id,
        'keywords': keywords,
        'abstract': abstract,
        'publication_type': 'preprint' if arxiv_id and not journal else 'journal',
        'featured': False,
        'citations': {
            'count': 0,
            'last_updated': datetime.now().strftime('%Y-%m-%d'),
            'source': 'manual'
        },
        'metadata': {
            'added_date': datetime.now().strftime('%Y-%m-%d'),
            'last_updated': datetime.now().strftime('%Y-%m-%d'),
            'data_sources': ['manual'],
            'quality_score': 0.8,
            'review_status': 'pending'
        }
    }

    # Auto-classify
    classification = classify_paper(entry, TAXONOMY_PATH)
    entry['classification'] = classification

    # Remove None values
    entry = {k: v for k, v in entry.items() if v is not None}

    return _save_entry(entry, interactive=True)


def add_paper(doi: Optional[str] = None,
              arxiv_id: Optional[str] = None,
              interactive: bool = False) -> bool:
    """
    Add a paper to the database.

    Args:
        doi: Digital Object Identifier
        arxiv_id: arXiv identifier
        interactive: Whether to prompt for confirmation

    Returns:
        True if paper was added successfully
    """
    if not doi and not arxiv_id:
        logger.error("Must provide either DOI or arXiv ID")
        return False

    # Load database
    db = load_database(DATABASE_PATH)

    # Check for existing entry
    if doi:
        existing = find_by_doi(db, doi)
        if existing:
            logger.error(f"Paper already exists: {existing.get('title')}")
            return False

    if arxiv_id:
        existing = find_by_arxiv(db, arxiv_id)
        if existing:
            logger.error(f"Paper already exists: {existing.get('title')}")
            return False

    # Fetch metadata
    metadata = fetch_paper_metadata(doi=doi, arxiv_id=arxiv_id)
    if not metadata:
        return False

    # Create entry
    entry = create_entry_from_metadata(metadata)

    return _save_entry(entry, interactive=interactive)


def _save_entry(entry: Dict[str, Any], interactive: bool = False) -> bool:
    """
    Validate and save entry to database.

    Args:
        entry: Entry dictionary
        interactive: Whether to prompt for confirmation

    Returns:
        True if saved successfully
    """
    # Validate entry
    validation = validate_entry(entry)
    if not validation.is_valid:
        logger.error("Entry validation failed:")
        print(generate_validation_report(validation))
        return False

    if validation.warning_count > 0:
        logger.warning(f"Entry has {validation.warning_count} warnings")

    # Display entry for review
    print("\n" + "─" * 60)
    print("PAPER TO ADD:")
    print("─" * 60)
    print(f"Title: {entry.get('title')}")
    print(f"Authors: {', '.join(a.get('name', '') for a in entry.get('authors', []))}")
    print(f"Year: {entry.get('year')}")
    print(f"Journal: {entry.get('journal', 'N/A')}")
    print(f"DOI: {entry.get('doi', 'N/A')}")
    print(f"arXiv: {entry.get('arxiv_id', 'N/A')}")
    print(f"Keywords: {', '.join(entry.get('keywords', []))}")

    classification = entry.get('classification', {})
    print(f"\nClassification:")
    print(f"  Research Area: {classification.get('research_area', 'N/A')}")
    print(f"  Source Types: {', '.join(classification.get('source_types', [])) or 'N/A'}")
    print(f"  Relevance Score: {classification.get('relevance_score', 0):.2f}")
    print("─" * 60)

    # Confirm if interactive
    if interactive:
        confirm = input("\nAdd this paper? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Cancelled.")
            return False

    # Load and update database
    db = load_database(DATABASE_PATH)
    success, message = add_entry(db, entry)

    if success:
        save_database(db, DATABASE_PATH)
        logger.info(message)
        print(f"\n✅ {message}")
        print(f"Entry ID: {entry.get('entry_id')}")
        return True
    else:
        logger.error(message)
        print(f"\n❌ {message}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Add paper to Taiji Publications Database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/add_paper.py --doi 10.1103/PhysRevD.100.022003
    python scripts/add_paper.py --arxiv 2401.12345
    python scripts/add_paper.py --interactive
        """
    )

    parser.add_argument('--doi', help='DOI of the paper')
    parser.add_argument('--arxiv', help='arXiv ID of the paper')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Interactive mode')
    parser.add_argument('--yes', '-y', action='store_true',
                        help='Skip confirmation prompt')

    args = parser.parse_args()

    if args.interactive:
        success = interactive_add()
    elif args.doi or args.arxiv:
        success = add_paper(
            doi=args.doi,
            arxiv_id=args.arxiv,
            interactive=not args.yes
        )
    else:
        parser.print_help()
        success = False

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
