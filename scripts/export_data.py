#!/usr/bin/env python3
"""
Export Taiji Publications Database to Various Formats
导出太极出版物数据库到多种格式

Supported formats:
- BibTeX (.bib)
- CSV (.csv)
- Markdown (.md)
- JSON (.json)

Usage:
    python scripts/export_data.py --all
    python scripts/export_data.py --format bibtex --output papers.bib
    python scripts/export_data.py --format csv --output papers.csv
"""

import sys
import json
import csv
import argparse
import logging
import re
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
OUTPUT_DIR = Path("database")


def generate_bibtex_key(entry: Dict[str, Any]) -> str:
    """
    Generate a BibTeX key for an entry.

    Args:
        entry: Paper entry dictionary

    Returns:
        BibTeX key string
    """
    # Get first author last name
    authors = entry.get('authors', [])
    if authors:
        first_author = authors[0].get('name', 'Unknown')
        # Extract last name (assume "First Last" or "Last, First" format)
        if ',' in first_author:
            last_name = first_author.split(',')[0].strip()
        else:
            last_name = first_author.split()[-1] if first_author.split() else 'Unknown'
    else:
        last_name = 'Unknown'

    # Clean the name (remove special characters)
    last_name = re.sub(r'[^a-zA-Z]', '', last_name)

    year = entry.get('year', 'XXXX')

    # Add a unique suffix from title
    title = entry.get('title', '')
    title_word = re.sub(r'[^a-zA-Z]', '', title.split()[0] if title.split() else 'paper')

    return f"{last_name}{year}{title_word}"


def entry_to_bibtex(entry: Dict[str, Any]) -> str:
    """
    Convert an entry to BibTeX format.

    Args:
        entry: Paper entry dictionary

    Returns:
        BibTeX string
    """
    # Determine entry type
    pub_type = entry.get('publication_type', 'article')
    if pub_type == 'preprint':
        bibtex_type = 'unpublished'
    elif pub_type == 'conference':
        bibtex_type = 'inproceedings'
    else:
        bibtex_type = 'article'

    key = generate_bibtex_key(entry)

    lines = [f"@{bibtex_type}{{{key},"]

    # Title
    title = entry.get('title', '')
    lines.append(f'  title = {{{title}}},')

    # Authors
    authors = entry.get('authors', [])
    author_str = ' and '.join(a.get('name', '') for a in authors)
    lines.append(f'  author = {{{author_str}}},')

    # Year
    year = entry.get('year', '')
    lines.append(f'  year = {{{year}}},')

    # Journal/booktitle
    journal = entry.get('journal', '')
    if journal:
        if bibtex_type == 'inproceedings':
            lines.append(f'  booktitle = {{{journal}}},')
        else:
            lines.append(f'  journal = {{{journal}}},')

    # Volume
    volume = entry.get('volume', '')
    if volume:
        lines.append(f'  volume = {{{volume}}},')

    # Pages
    pages = entry.get('pages', '')
    if pages:
        lines.append(f'  pages = {{{pages}}},')

    # DOI
    doi = entry.get('doi', '')
    if doi:
        lines.append(f'  doi = {{{doi}}},')

    # arXiv
    arxiv_id = entry.get('arxiv_id', '')
    if arxiv_id:
        lines.append(f'  eprint = {{{arxiv_id}}},')
        lines.append('  archiveprefix = {arXiv},')

    # Abstract
    abstract = entry.get('abstract', '')
    if abstract:
        # Escape special characters
        abstract = abstract.replace('{', '\\{').replace('}', '\\}')
        lines.append(f'  abstract = {{{abstract}}},')

    # Keywords
    keywords = entry.get('keywords', [])
    if keywords:
        kw_str = ', '.join(keywords)
        lines.append(f'  keywords = {{{kw_str}}},')

    lines.append('}')

    return '\n'.join(lines)


def export_bibtex(entries: List[Dict[str, Any]], output_path: Path):
    """
    Export entries to BibTeX format.

    Args:
        entries: List of paper entries
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"% Taiji Publications Database\n")
        f.write(f"% Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"% Total entries: {len(entries)}\n\n")

        for entry in entries:
            f.write(entry_to_bibtex(entry))
            f.write('\n\n')

    logger.info(f"Exported {len(entries)} entries to {output_path}")


def export_csv(entries: List[Dict[str, Any]], output_path: Path):
    """
    Export entries to CSV format.

    Args:
        entries: List of paper entries
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        'entry_id', 'title', 'authors', 'year', 'journal', 'volume', 'pages',
        'doi', 'arxiv_id', 'keywords', 'publication_type', 'featured',
        'citation_count', 'research_area', 'relevance_score', 'abstract'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for entry in entries:
            row = {
                'entry_id': entry.get('entry_id', ''),
                'title': entry.get('title', ''),
                'authors': '; '.join(a.get('name', '') for a in entry.get('authors', [])),
                'year': entry.get('year', ''),
                'journal': entry.get('journal', ''),
                'volume': entry.get('volume', ''),
                'pages': entry.get('pages', ''),
                'doi': entry.get('doi', ''),
                'arxiv_id': entry.get('arxiv_id', ''),
                'keywords': '; '.join(entry.get('keywords', [])),
                'publication_type': entry.get('publication_type', ''),
                'featured': entry.get('featured', False),
                'citation_count': entry.get('citations', {}).get('count', 0),
                'research_area': entry.get('classification', {}).get('research_area', ''),
                'relevance_score': entry.get('classification', {}).get('relevance_score', 0),
                'abstract': entry.get('abstract', '')[:500] if entry.get('abstract') else ''
            }
            writer.writerow(row)

    logger.info(f"Exported {len(entries)} entries to {output_path}")


def export_markdown(entries: List[Dict[str, Any]], output_path: Path):
    """
    Export entries to Markdown format.

    Args:
        entries: List of paper entries
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        '# Taiji Publications Database',
        '',
        f'Exported: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        f'Total entries: {len(entries)}',
        '',
        '---',
        ''
    ]

    # Group by year
    by_year = {}
    for entry in entries:
        year = entry.get('year', 'Unknown')
        if year not in by_year:
            by_year[year] = []
        by_year[year].append(entry)

    for year in sorted(by_year.keys(), reverse=True):
        lines.append(f'## {year}')
        lines.append('')

        for entry in by_year[year]:
            title = entry.get('title', 'Untitled')
            authors = entry.get('authors', [])
            author_str = authors[0].get('name', 'Unknown') if authors else 'Unknown'
            if len(authors) > 1:
                author_str += ' et al.'

            journal = entry.get('journal', '')
            doi = entry.get('doi', '')
            arxiv = entry.get('arxiv_id', '')

            lines.append(f'### {title}')
            lines.append('')
            lines.append(f'**Authors:** {author_str}')
            if journal:
                lines.append(f'**Journal:** {journal}')
            if doi:
                lines.append(f'**DOI:** [{doi}](https://doi.org/{doi})')
            if arxiv:
                lines.append(f'**arXiv:** [{arxiv}](https://arxiv.org/abs/{arxiv})')

            keywords = entry.get('keywords', [])
            if keywords:
                lines.append(f'**Keywords:** {", ".join(keywords)}')

            abstract = entry.get('abstract', '')
            if abstract:
                lines.append('')
                lines.append(f'> {abstract[:300]}{"..." if len(abstract) > 300 else ""}')

            lines.append('')
            lines.append('---')
            lines.append('')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    logger.info(f"Exported {len(entries)} entries to {output_path}")


def export_json(entries: List[Dict[str, Any]], output_path: Path):
    """
    Export entries to JSON format (clean version).

    Args:
        entries: List of paper entries
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output = {
        'metadata': {
            'exported': datetime.now().isoformat(),
            'total_entries': len(entries)
        },
        'entries': entries
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info(f"Exported {len(entries)} entries to {output_path}")


def export_all(entries: List[Dict[str, Any]], output_dir: Path):
    """
    Export entries to all supported formats.

    Args:
        entries: List of paper entries
        output_dir: Output directory
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    export_bibtex(entries, output_dir / 'papers.bib')
    export_csv(entries, output_dir / 'papers.csv')
    export_markdown(entries, output_dir / 'papers.md')
    export_json(entries, output_dir / 'papers.json')


def main():
    parser = argparse.ArgumentParser(
        description='Export Taiji Publications Database to various formats',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/export_data.py --all
    python scripts/export_data.py --format bibtex --output papers.bib
    python scripts/export_data.py --format csv --output papers.csv
    python scripts/export_data.py --format markdown --output papers.md
        """
    )

    parser.add_argument('--all', action='store_true',
                        help='Export to all formats')
    parser.add_argument('--format', choices=['bibtex', 'csv', 'markdown', 'json'],
                        help='Export format')
    parser.add_argument('--output', '-o', type=Path,
                        help='Output file path')
    parser.add_argument('--output-dir', type=Path, default=OUTPUT_DIR,
                        help='Output directory for --all (default: database/)')

    args = parser.parse_args()

    # Load database
    db = load_database(DATABASE_PATH)
    entries = get_all_entries(db)

    print(f"\nLoaded {len(entries)} entries from database\n")

    if args.all:
        export_all(entries, args.output_dir)
        print(f"\n✅ Exported to all formats in {args.output_dir}/")

    elif args.format:
        output = args.output
        if not output:
            suffix_map = {
                'bibtex': '.bib',
                'csv': '.csv',
                'markdown': '.md',
                'json': '.json'
            }
            output = OUTPUT_DIR / f"papers{suffix_map[args.format]}"

        if args.format == 'bibtex':
            export_bibtex(entries, output)
        elif args.format == 'csv':
            export_csv(entries, output)
        elif args.format == 'markdown':
            export_markdown(entries, output)
        elif args.format == 'json':
            export_json(entries, output)

        print(f"\n✅ Exported to {output}")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
