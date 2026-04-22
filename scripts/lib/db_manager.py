#!/usr/bin/env python3
"""
Database Manager for Taiji Publications
太极出版物数据库管理器

Provides functions for:
- Loading and saving the JSON database
- Finding entries by DOI, arXiv ID, or title
- Adding and updating entries
- Generating unique entry IDs
"""

import json
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default paths
DEFAULT_DATABASE_PATH = Path("data/papers.json")
DEFAULT_SCHEMA_PATH = Path("config/schema.json")


# ═══════════════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Author:
    """Author information."""
    name: str
    affiliation: Optional[str] = None
    orcid: Optional[str] = None
    email: Optional[str] = None


@dataclass
class Classification:
    """Paper classification."""
    research_area: Optional[str] = None
    source_types: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    relevance_score: float = 0.0


@dataclass
class Citations:
    """Citation information."""
    count: int = 0
    last_updated: Optional[str] = None
    source: str = "manual"
    citing_papers: List[str] = field(default_factory=list)


@dataclass
class EntryMetadata:
    """Entry metadata."""
    added_date: Optional[str] = None
    last_updated: Optional[str] = None
    data_sources: List[str] = field(default_factory=list)
    quality_score: float = 1.0
    review_status: str = "pending"
    notes: Optional[str] = None


@dataclass
class PaperEntry:
    """A single paper entry in the database."""
    entry_id: str
    title: str
    authors: List[Dict[str, Any]]
    year: int

    # Optional fields
    journal: Optional[str] = None
    volume: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    publication_type: str = "journal"
    featured: bool = False

    # Nested objects
    classification: Optional[Dict[str, Any]] = None
    citations: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        # Remove None values
        return {k: v for k, v in result.items() if v is not None}


# ═══════════════════════════════════════════════════════════════════════════════
# Database Loading and Saving
# ═══════════════════════════════════════════════════════════════════════════════

def load_database(path: Path = DEFAULT_DATABASE_PATH) -> Dict[str, Any]:
    """
    Load the papers database from JSON file.

    Args:
        path: Path to the database file

    Returns:
        Database dictionary with 'metadata' and 'entries' keys
    """
    if not path.exists():
        logger.warning(f"Database file not found: {path}")
        return create_empty_database()

    try:
        with open(path, 'r', encoding='utf-8') as f:
            db = json.load(f)

        logger.info(f"Loaded database with {len(db.get('entries', []))} entries")
        return db

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing database JSON: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading database: {e}")
        raise


def save_database(db: Dict[str, Any], path: Path = DEFAULT_DATABASE_PATH,
                  backup: bool = True) -> None:
    """
    Save the papers database to JSON file.

    Args:
        db: Database dictionary
        path: Path to save to
        backup: Whether to create a backup before saving
    """
    # Create backup if requested and file exists
    if backup and path.exists():
        backup_path = path.with_suffix(f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        path.rename(backup_path)
        logger.info(f"Created backup: {backup_path}")

    # Update metadata
    db['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    db['metadata']['total_entries'] = len(db.get('entries', []))

    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Save with pretty formatting
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved database with {db['metadata']['total_entries']} entries to {path}")


def create_empty_database() -> Dict[str, Any]:
    """Create a new empty database structure."""
    return {
        "metadata": {
            "version": "1.0",
            "project": "Taiji Publications",
            "created_date": datetime.now().strftime('%Y-%m-%d'),
            "last_updated": datetime.now().strftime('%Y-%m-%d'),
            "total_entries": 0,
            "description": "太极空间引力波探测项目出版物数据库"
        },
        "entries": []
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Entry ID Generation
# ═══════════════════════════════════════════════════════════════════════════════

def generate_entry_id(doi: Optional[str] = None, arxiv_id: Optional[str] = None,
                      title: Optional[str] = None, year: Optional[int] = None) -> str:
    """
    Generate a unique entry ID for a paper.

    Priority:
    1. DOI (if available)
    2. arXiv ID (prefixed with 'arxiv:')
    3. Slug from title + year

    Args:
        doi: Digital Object Identifier
        arxiv_id: arXiv identifier
        title: Paper title
        year: Publication year

    Returns:
        Unique entry ID string
    """
    if doi:
        return doi

    if arxiv_id:
        return f"arxiv:{arxiv_id}"

    if title:
        # Generate slug from title
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug).strip('-')
        slug = slug[:50]  # Limit length

        if year:
            return f"{year}-{slug}"
        return slug

    raise ValueError("Cannot generate entry ID: need DOI, arXiv ID, or title")


# ═══════════════════════════════════════════════════════════════════════════════
# Finding Entries
# ═══════════════════════════════════════════════════════════════════════════════

def find_by_doi(db: Dict[str, Any], doi: str) -> Optional[Dict[str, Any]]:
    """
    Find an entry by DOI.

    Args:
        db: Database dictionary
        doi: DOI to search for

    Returns:
        Entry dictionary if found, None otherwise
    """
    # Normalize DOI
    doi = doi.lower().strip()
    if doi.startswith('https://doi.org/'):
        doi = doi[16:]
    elif doi.startswith('http://dx.doi.org/'):
        doi = doi[18:]

    for entry in db.get('entries', []):
        entry_doi = (entry.get('doi') or '').lower()
        entry_id = (entry.get('entry_id') or '').lower()

        if entry_doi == doi or entry_id == doi:
            return entry

    return None


def find_by_arxiv(db: Dict[str, Any], arxiv_id: str) -> Optional[Dict[str, Any]]:
    """
    Find an entry by arXiv ID.

    Args:
        db: Database dictionary
        arxiv_id: arXiv ID to search for (e.g., "2401.12345")

    Returns:
        Entry dictionary if found, None otherwise
    """
    # Normalize arXiv ID (remove version number for comparison)
    clean_id = arxiv_id.split('v')[0].lower().strip()

    for entry in db.get('entries', []):
        entry_arxiv = (entry.get('arxiv_id') or '').split('v')[0].lower()
        entry_id = (entry.get('entry_id') or '').lower()

        if entry_arxiv == clean_id or entry_id == f"arxiv:{clean_id}":
            return entry

    return None


def find_by_title(db: Dict[str, Any], title: str, threshold: float = 0.85) -> List[Tuple[Dict[str, Any], float]]:
    """
    Find entries by title similarity.

    Args:
        db: Database dictionary
        title: Title to search for
        threshold: Minimum similarity score (0-1)

    Returns:
        List of (entry, similarity_score) tuples, sorted by score descending
    """
    try:
        from Levenshtein import ratio
    except ImportError:
        logger.warning("python-Levenshtein not installed, using basic comparison")
        # Fallback to basic comparison
        def ratio(s1, s2):
            s1 = s1.lower()
            s2 = s2.lower()
            return 1.0 if s1 == s2 else 0.0

    results = []
    title_lower = title.lower().strip()

    for entry in db.get('entries', []):
        entry_title = entry.get('title', '').lower().strip()
        score = ratio(title_lower, entry_title)

        if score >= threshold:
            results.append((entry, score))

    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def find_by_id(db: Dict[str, Any], entry_id: str) -> Optional[Dict[str, Any]]:
    """
    Find an entry by its entry_id.

    Args:
        db: Database dictionary
        entry_id: Entry ID to search for

    Returns:
        Entry dictionary if found, None otherwise
    """
    entry_id_lower = entry_id.lower()

    for entry in db.get('entries', []):
        if entry.get('entry_id', '').lower() == entry_id_lower:
            return entry

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Adding and Updating Entries
# ═══════════════════════════════════════════════════════════════════════════════

def add_entry(db: Dict[str, Any], entry: Dict[str, Any],
              check_duplicates: bool = True) -> Tuple[bool, str]:
    """
    Add a new entry to the database.

    Args:
        db: Database dictionary
        entry: Entry dictionary to add
        check_duplicates: Whether to check for duplicates

    Returns:
        Tuple of (success, message)
    """
    # Validate required fields
    required_fields = ['entry_id', 'title', 'authors', 'year']
    for field in required_fields:
        if field not in entry:
            return False, f"Missing required field: {field}"

    # Check for duplicates
    if check_duplicates:
        # Check by DOI
        if entry.get('doi'):
            existing = find_by_doi(db, entry['doi'])
            if existing:
                return False, f"Duplicate DOI found: {entry['doi']}"

        # Check by arXiv ID
        if entry.get('arxiv_id'):
            existing = find_by_arxiv(db, entry['arxiv_id'])
            if existing:
                return False, f"Duplicate arXiv ID found: {entry['arxiv_id']}"

        # Check by entry_id
        existing = find_by_id(db, entry['entry_id'])
        if existing:
            return False, f"Duplicate entry ID found: {entry['entry_id']}"

        # Check by title (fuzzy)
        similar = find_by_title(db, entry['title'], threshold=0.95)
        if similar:
            existing_title = similar[0][0]['title']
            return False, f"Similar title found ({similar[0][1]:.0%}): {existing_title}"

    # Add metadata if not present
    if 'metadata' not in entry:
        entry['metadata'] = {}

    entry['metadata']['added_date'] = datetime.now().strftime('%Y-%m-%d')
    entry['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')

    # Add to database
    db['entries'].append(entry)

    logger.info(f"Added entry: {entry['entry_id']}")
    return True, f"Successfully added: {entry['title']}"


def update_entry(db: Dict[str, Any], entry_id: str,
                 updates: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Update an existing entry.

    Args:
        db: Database dictionary
        entry_id: Entry ID to update
        updates: Dictionary of fields to update

    Returns:
        Tuple of (success, message)
    """
    entry = find_by_id(db, entry_id)
    if not entry:
        return False, f"Entry not found: {entry_id}"

    # Update fields
    for key, value in updates.items():
        if key == 'entry_id':
            continue  # Don't update entry_id

        if isinstance(value, dict) and key in entry and isinstance(entry[key], dict):
            # Merge dictionaries
            entry[key].update(value)
        else:
            entry[key] = value

    # Update last_updated
    if 'metadata' not in entry:
        entry['metadata'] = {}
    entry['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')

    logger.info(f"Updated entry: {entry_id}")
    return True, f"Successfully updated: {entry_id}"


def delete_entry(db: Dict[str, Any], entry_id: str) -> Tuple[bool, str]:
    """
    Delete an entry from the database.

    Args:
        db: Database dictionary
        entry_id: Entry ID to delete

    Returns:
        Tuple of (success, message)
    """
    entry_id_lower = entry_id.lower()

    for i, entry in enumerate(db.get('entries', [])):
        if entry.get('entry_id', '').lower() == entry_id_lower:
            deleted = db['entries'].pop(i)
            logger.info(f"Deleted entry: {entry_id}")
            return True, f"Deleted: {deleted['title']}"

    return False, f"Entry not found: {entry_id}"


# ═══════════════════════════════════════════════════════════════════════════════
# Database Queries
# ═══════════════════════════════════════════════════════════════════════════════

def get_all_entries(db: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get all entries from the database."""
    return db.get('entries', [])


def get_entries_by_year(db: Dict[str, Any], year: int) -> List[Dict[str, Any]]:
    """Get all entries from a specific year."""
    return [e for e in db.get('entries', []) if e.get('year') == year]


def get_entries_by_keyword(db: Dict[str, Any], keyword: str) -> List[Dict[str, Any]]:
    """Get all entries containing a specific keyword."""
    keyword_lower = keyword.lower()
    return [
        e for e in db.get('entries', [])
        if keyword_lower in [k.lower() for k in e.get('keywords', [])]
    ]


def get_entries_by_author(db: Dict[str, Any], author_name: str) -> List[Dict[str, Any]]:
    """Get all entries by a specific author."""
    author_lower = author_name.lower()
    results = []

    for entry in db.get('entries', []):
        for author in entry.get('authors', []):
            if author_lower in author.get('name', '').lower():
                results.append(entry)
                break

    return results


def get_statistics(db: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get database statistics.

    Returns:
        Dictionary with various statistics
    """
    entries = db.get('entries', [])

    # Year distribution
    years = {}
    for entry in entries:
        year = entry.get('year')
        if year:
            years[year] = years.get(year, 0) + 1

    # Publication type distribution
    types = {}
    for entry in entries:
        pub_type = entry.get('publication_type', 'unknown')
        types[pub_type] = types.get(pub_type, 0) + 1

    # Keyword frequency
    keywords = {}
    for entry in entries:
        for kw in entry.get('keywords', []):
            kw_lower = kw.lower()
            keywords[kw_lower] = keywords.get(kw_lower, 0) + 1

    # Sort keywords by frequency
    top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:20]

    # Research areas
    areas = {}
    for entry in entries:
        area = entry.get('classification', {}).get('research_area')
        if area:
            areas[area] = areas.get(area, 0) + 1

    # Total citations
    total_citations = sum(
        entry.get('citations', {}).get('count', 0)
        for entry in entries
    )

    return {
        'total_entries': len(entries),
        'years': dict(sorted(years.items())),
        'publication_types': types,
        'top_keywords': dict(top_keywords),
        'research_areas': areas,
        'total_citations': total_citations,
        'entries_with_doi': sum(1 for e in entries if e.get('doi')),
        'entries_with_arxiv': sum(1 for e in entries if e.get('arxiv_id')),
        'entries_with_abstract': sum(1 for e in entries if e.get('abstract')),
        'featured_count': sum(1 for e in entries if e.get('featured'))
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CLI for testing
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Database manager CLI')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--find-doi', help='Find entry by DOI')
    parser.add_argument('--find-arxiv', help='Find entry by arXiv ID')
    parser.add_argument('--find-title', help='Find entry by title')
    parser.add_argument('--list', action='store_true', help='List all entries')

    args = parser.parse_args()

    db = load_database()

    if args.stats:
        stats = get_statistics(db)
        print(json.dumps(stats, indent=2, ensure_ascii=False))

    elif args.find_doi:
        entry = find_by_doi(db, args.find_doi)
        if entry:
            print(json.dumps(entry, indent=2, ensure_ascii=False))
        else:
            print(f"Not found: {args.find_doi}")

    elif args.find_arxiv:
        entry = find_by_arxiv(db, args.find_arxiv)
        if entry:
            print(json.dumps(entry, indent=2, ensure_ascii=False))
        else:
            print(f"Not found: {args.find_arxiv}")

    elif args.find_title:
        results = find_by_title(db, args.find_title)
        if results:
            for entry, score in results:
                print(f"[{score:.0%}] {entry['title']}")
        else:
            print(f"No matches found for: {args.find_title}")

    elif args.list:
        for entry in db.get('entries', []):
            print(f"[{entry.get('year')}] {entry['title']}")
            print(f"  ID: {entry['entry_id']}")
            print()

    else:
        parser.print_help()
