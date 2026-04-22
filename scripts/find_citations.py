#!/usr/bin/env python3
"""
Find Citations for Papers in Taiji Publications Database
查找太极出版物数据库中论文的引用

This script finds papers that cite a given paper and evaluates their
relevance to the Taiji project.

Usage:
    python scripts/find_citations.py --arxiv 2401.12345
    python scripts/find_citations.py --arxiv 2401.12345 --auto --limit 10 --min-relevance 0.5
    python scripts/find_citations.py --arxiv 2401.12345 --dry-run
"""

import sys
import json
import csv
import argparse
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.api_client import SemanticScholarClient, ArxivClient, PaperFetcher
from lib.db_manager import (
    load_database, save_database, add_entry, find_by_doi, find_by_arxiv,
    find_by_id, generate_entry_id
)
from lib.classifier import TaijiRelevanceScorer, classify_paper, ClassificationResult
from lib.validator import validate_entry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
DATABASE_PATH = Path("data/papers.json")
TAXONOMY_PATH = Path("config/taxonomy.yaml")
CACHE_PATH = Path("data/citations_cache.json")


class CitationFinder:
    """Find and analyze citations for papers."""

    def __init__(self):
        self.s2_client = SemanticScholarClient()
        self.arxiv_client = ArxivClient()
        self.fetcher = PaperFetcher()
        self.scorer = TaijiRelevanceScorer(TAXONOMY_PATH)
        self.db = load_database(DATABASE_PATH)

    def find_citations(self, arxiv_id: Optional[str] = None,
                       doi: Optional[str] = None,
                       limit: int = 100) -> List[Dict[str, Any]]:
        """
        Find papers that cite the given paper.

        Args:
            arxiv_id: arXiv identifier
            doi: Digital Object Identifier
            limit: Maximum number of citations to fetch

        Returns:
            List of citing paper metadata
        """
        if arxiv_id:
            logger.info(f"Finding citations for arXiv:{arxiv_id}")
            response = self.s2_client.get_citations(arxiv_id, id_type='arxiv', limit=limit)
        elif doi:
            logger.info(f"Finding citations for DOI:{doi}")
            response = self.s2_client.get_citations(doi, id_type='doi', limit=limit)
        else:
            logger.error("Must provide either arXiv ID or DOI")
            return []

        if not response.success:
            logger.error(f"Failed to fetch citations: {response.error}")
            return []

        citations = response.data.get('citations', [])
        logger.info(f"Found {len(citations)} citing papers")

        return citations

    def score_citations(self, citations: List[Dict[str, Any]],
                        min_relevance: float = 0.0) -> List[Tuple[Dict[str, Any], float, str]]:
        """
        Score citations for Taiji relevance.

        Args:
            citations: List of citing paper metadata
            min_relevance: Minimum relevance score to include

        Returns:
            List of (paper, score, explanation) tuples, sorted by score
        """
        scored = []

        for citation in citations:
            title = citation.get('title', '')
            abstract = citation.get('abstract', '')

            score, matched, explanation = self.scorer.compute_relevance_score(
                title, abstract
            )

            if score >= min_relevance:
                scored.append((citation, score, explanation))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored

    def check_existing(self, citation: Dict[str, Any]) -> bool:
        """
        Check if a citation already exists in the database.

        Args:
            citation: Citation metadata

        Returns:
            True if already exists
        """
        # Check by DOI
        external_ids = citation.get('external_ids') or {}
        doi = external_ids.get('DOI')
        if doi:
            if find_by_doi(self.db, doi):
                return True

        # Check by arXiv ID
        arxiv_id = external_ids.get('ArXiv')
        if arxiv_id:
            if find_by_arxiv(self.db, arxiv_id):
                return True

        return False

    def add_citation_to_db(self, citation: Dict[str, Any],
                           fast_mode: bool = False) -> Tuple[bool, str]:
        """
        Add a citation to the database.

        Args:
            citation: Citation metadata from Semantic Scholar
            fast_mode: If True, skip arXiv/Crossref API calls and use S2 data directly

        Returns:
            Tuple of (success, message)
        """
        external_ids = citation.get('external_ids') or {}
        arxiv_id = external_ids.get('ArXiv')
        doi = external_ids.get('DOI')

        metadata = None

        if not fast_mode:
            # Try to get full metadata with error handling
            try:
                if arxiv_id:
                    metadata = self.fetcher.fetch_by_arxiv(arxiv_id)
                elif doi:
                    metadata = self.fetcher.fetch_by_doi(doi)
            except Exception as e:
                logger.warning(f"Failed to fetch metadata: {e}")
                metadata = None

        # Fallback (or fast mode): Use Semantic Scholar data directly
        if not metadata:
            metadata = {
                'title': citation.get('title'),
                'authors': citation.get('authors', []),
                'year': citation.get('year'),
                'abstract': citation.get('abstract'),
                'citation_count': citation.get('citation_count', 0),
                'doi': doi,
                'arxiv_id': arxiv_id,
                'data_sources': ['semantic_scholar']
            }

        # Generate entry ID
        entry_id = generate_entry_id(
            doi=metadata.get('doi'),
            arxiv_id=metadata.get('arxiv_id'),
            title=metadata.get('title'),
            year=metadata.get('year')
        )

        # Create entry
        entry = {
            'entry_id': entry_id,
            'title': metadata.get('title', '').strip(),
            'authors': [
                {'name': a.get('name', ''), 'affiliation': a.get('affiliation')}
                for a in metadata.get('authors', [])
            ],
            'year': metadata.get('year'),
            'journal': metadata.get('journal'),
            'volume': metadata.get('volume'),
            'pages': metadata.get('pages'),
            'doi': metadata.get('doi'),
            'arxiv_id': metadata.get('arxiv_id'),
            'abstract': metadata.get('abstract'),
            'keywords': metadata.get('keywords', []),
            'publication_type': 'preprint' if metadata.get('arxiv_id') and not metadata.get('journal') else 'journal',
            'featured': False,
            'citations': {
                'count': metadata.get('citation_count', 0),
                'last_updated': datetime.now().strftime('%Y-%m-%d'),
                'source': 'semantic_scholar'
            },
            'metadata': {
                'added_date': datetime.now().strftime('%Y-%m-%d'),
                'last_updated': datetime.now().strftime('%Y-%m-%d'),
                'data_sources': metadata.get('data_sources', ['semantic_scholar']),
                'quality_score': 0.9,
                'review_status': 'pending',
                'notes': 'Added via citation tracking'
            }
        }

        # Auto-classify
        entry['classification'] = classify_paper(entry, TAXONOMY_PATH)

        # Remove None values
        entry = {k: v for k, v in entry.items() if v is not None}

        # Validate
        validation = validate_entry(entry)
        if not validation.is_valid:
            return False, f"Validation failed: {validation.error_count} errors"

        # Add to database
        success, message = add_entry(self.db, entry)

        return success, message

    def save_results_csv(self, scored_citations: List[Tuple[Dict, float, str]],
                         output_path: Path):
        """
        Save scored citations to CSV file.

        Args:
            scored_citations: List of (paper, score, explanation) tuples
            output_path: Path to output CSV file
        """
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Title', 'Year', 'Authors', 'Relevance Score', 'Explanation',
                'DOI', 'arXiv', 'Citation Count', 'In Database'
            ])

            for citation, score, explanation in scored_citations:
                authors = ', '.join(
                    a.get('name', '') for a in citation.get('authors', [])[:3]
                )
                if len(citation.get('authors', [])) > 3:
                    authors += ' et al.'

                external_ids = citation.get('external_ids', {})

                writer.writerow([
                    citation.get('title', ''),
                    citation.get('year', ''),
                    authors,
                    f"{score:.2f}",
                    explanation,
                    external_ids.get('DOI', ''),
                    external_ids.get('ArXiv', ''),
                    citation.get('citation_count', 0),
                    'Yes' if self.check_existing(citation) else 'No'
                ])

        logger.info(f"Saved results to {output_path}")

    def save_database(self):
        """Save the database to file."""
        save_database(self.db, DATABASE_PATH)


def display_citation(citation: Dict[str, Any], score: float, explanation: str,
                     index: int, in_db: bool):
    """Display a citation in formatted output."""
    authors = citation.get('authors', [])
    author_str = authors[0].get('name', 'Unknown') if authors else 'Unknown'
    if len(authors) > 1:
        author_str += ' et al.'

    external_ids = citation.get('external_ids') or {}
    doi = external_ids.get('DOI', '')
    arxiv = external_ids.get('ArXiv', '')

    status = "✓ IN DB" if in_db else ""

    print(f"\n[{index}] Score: {score:.2f} {status}")
    print(f"    {citation.get('title', 'No title')}")
    print(f"    {author_str} ({citation.get('year', 'N/A')})")
    if doi:
        print(f"    DOI: {doi}")
    if arxiv:
        print(f"    arXiv: {arxiv}")
    print(f"    → {explanation}")


def main():
    parser = argparse.ArgumentParser(
        description='Find citations for papers in Taiji Publications Database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/find_citations.py --arxiv 2401.12345
    python scripts/find_citations.py --arxiv 2401.12345 --auto --limit 10
    python scripts/find_citations.py --arxiv 2401.12345 --min-relevance 0.5
    python scripts/find_citations.py --arxiv 2401.12345 --dry-run --csv output.csv
        """
    )

    parser.add_argument('--arxiv', help='arXiv ID of the source paper')
    parser.add_argument('--doi', help='DOI of the source paper')
    parser.add_argument('--limit', type=int, default=50,
                        help='Maximum number of citations to fetch (default: 50)')
    parser.add_argument('--min-relevance', type=float, default=0.0,
                        help='Minimum relevance score to display (default: 0.0)')
    parser.add_argument('--auto', action='store_true',
                        help='Automatically add papers above min-relevance')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be added without making changes')
    parser.add_argument('--csv', type=Path,
                        help='Export results to CSV file')
    parser.add_argument('--json', type=Path,
                        help='Export results to JSON file')
    parser.add_argument('--fast', action='store_true',
                        help='Fast mode: use Semantic Scholar data directly, skip arXiv/Crossref API calls')

    args = parser.parse_args()

    if not args.arxiv and not args.doi:
        parser.print_help()
        print("\nError: Must provide either --arxiv or --doi")
        sys.exit(1)

    # Initialize finder
    finder = CitationFinder()

    # Find citations
    citations = finder.find_citations(
        arxiv_id=args.arxiv,
        doi=args.doi,
        limit=args.limit
    )

    if not citations:
        print("No citations found.")
        sys.exit(0)

    # Score citations
    scored = finder.score_citations(citations, min_relevance=args.min_relevance)

    print("\n" + "=" * 70)
    print(f"CITATIONS FOR: {'arXiv:' + args.arxiv if args.arxiv else 'DOI:' + args.doi}")
    print(f"Found: {len(citations)} total, {len(scored)} with relevance >= {args.min_relevance}")
    print("=" * 70)

    # Export if requested
    if args.csv:
        finder.save_results_csv(scored, args.csv)

    if args.json:
        output = [{
            'title': c[0].get('title'),
            'year': c[0].get('year'),
            'score': c[1],
            'explanation': c[2],
            'external_ids': c[0].get('external_ids', {}),
            'in_database': finder.check_existing(c[0])
        } for c in scored]
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved JSON results to {args.json}")

    # Display results
    added_count = 0
    skipped_count = 0

    for i, (citation, score, explanation) in enumerate(scored, 1):
        in_db = finder.check_existing(citation)
        display_citation(citation, score, explanation, i, in_db)

        if in_db:
            skipped_count += 1
            continue

        # Auto-add or prompt
        if args.auto and not args.dry_run:
            try:
                success, message = finder.add_citation_to_db(citation, fast_mode=args.fast)
                if success:
                    print(f"    ✅ Added to database")
                    added_count += 1
                else:
                    print(f"    ❌ Failed: {message}")
                # Rate limiting: delay between API calls
                time.sleep(0.5)
            except Exception as e:
                print(f"    ❌ Error: {e}")
                time.sleep(1)  # Longer delay on error

        elif args.dry_run:
            print(f"    [DRY RUN] Would add to database")
            added_count += 1

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total citations found: {len(citations)}")
    print(f"Above relevance threshold: {len(scored)}")
    print(f"Already in database: {skipped_count}")

    if args.auto or args.dry_run:
        action = "Would add" if args.dry_run else "Added"
        print(f"{action}: {added_count}")

    # Save database if changes were made
    if args.auto and not args.dry_run and added_count > 0:
        finder.save_database()
        print(f"\n✅ Database saved with {added_count} new entries")

    # Interactive mode if not auto
    if not args.auto and not args.dry_run and len(scored) > 0:
        new_papers = [(c, s, e) for c, s, e in scored if not finder.check_existing(c)]
        if new_papers:
            print(f"\n{len(new_papers)} papers not in database.")
            add_all = input("Add all new papers above threshold? (y/n): ").strip().lower()

            if add_all == 'y':
                for citation, score, explanation in new_papers:
                    try:
                        success, message = finder.add_citation_to_db(citation, fast_mode=args.fast)
                        title = citation.get('title', 'Unknown')[:50]
                        if success:
                            print(f"  ✅ {title}...")
                            added_count += 1
                        else:
                            print(f"  ❌ {title}... ({message})")
                        time.sleep(0.5)  # Rate limiting
                    except Exception as e:
                        title = citation.get('title', 'Unknown')[:50]
                        print(f"  ❌ {title}... (Error: {e})")
                        time.sleep(1)

                if added_count > 0:
                    finder.save_database()
                    print(f"\n✅ Database saved with {added_count} new entries")


if __name__ == '__main__':
    main()
