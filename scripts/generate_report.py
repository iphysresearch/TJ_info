#!/usr/bin/env python3
"""
Generate Reports for Taiji Publications Database
生成太极出版物数据库报告

This script generates quality and statistics reports.

Usage:
    python scripts/generate_report.py
    python scripts/generate_report.py --output reports/report.json
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.db_manager import load_database, get_statistics
from lib.validator import check_quality, validate_database
from lib.classifier import TaijiRelevanceScorer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
DATABASE_PATH = Path("data/papers.json")
REPORTS_PATH = Path("reports")


def generate_full_report(db: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate comprehensive database report.

    Args:
        db: Database dictionary

    Returns:
        Report dictionary
    """
    entries = db.get('entries', [])

    # Statistics
    stats = get_statistics(db)

    # Quality metrics
    quality = check_quality(db)

    # Validation
    validation_result = validate_database(db)

    # Relevance distribution
    scorer = TaijiRelevanceScorer()
    relevance_scores = []
    for entry in entries:
        score = scorer.score_paper(entry)
        relevance_scores.append(score)

    if relevance_scores:
        avg_relevance = sum(relevance_scores) / len(relevance_scores)
        high_relevance = sum(1 for s in relevance_scores if s >= 0.8)
        medium_relevance = sum(1 for s in relevance_scores if 0.5 <= s < 0.8)
        low_relevance = sum(1 for s in relevance_scores if s < 0.5)
    else:
        avg_relevance = 0
        high_relevance = medium_relevance = low_relevance = 0

    # Citation analysis
    citation_counts = [
        entry.get('citations', {}).get('count', 0)
        for entry in entries
    ]
    if citation_counts:
        avg_citations = sum(citation_counts) / len(citation_counts)
        max_citations = max(citation_counts)
        highly_cited = sum(1 for c in citation_counts if c >= 10)
    else:
        avg_citations = max_citations = highly_cited = 0

    # Recent activity (papers from last 2 years)
    current_year = datetime.now().year
    recent_papers = sum(1 for e in entries if e.get('year', 0) >= current_year - 1)

    return {
        'metadata': {
            'generated': datetime.now().isoformat(),
            'database_version': db.get('metadata', {}).get('version', 'unknown'),
            'database_updated': db.get('metadata', {}).get('last_updated', 'unknown')
        },
        'summary': {
            'total_entries': stats['total_entries'],
            'featured_entries': stats['featured_count'],
            'total_citations': stats['total_citations'],
            'recent_papers': recent_papers
        },
        'statistics': {
            'by_year': stats['years'],
            'by_type': stats['publication_types'],
            'by_research_area': stats.get('research_areas', {}),
            'top_keywords': stats['top_keywords']
        },
        'quality': {
            'overall_score': quality['quality_score'],
            'completeness': quality['completeness'],
            'issues': quality['issues']
        },
        'validation': {
            'is_valid': validation_result.is_valid,
            'error_count': validation_result.error_count,
            'warning_count': validation_result.warning_count
        },
        'relevance': {
            'average_score': round(avg_relevance, 3),
            'high_relevance_count': high_relevance,
            'medium_relevance_count': medium_relevance,
            'low_relevance_count': low_relevance
        },
        'citations': {
            'average': round(avg_citations, 1),
            'maximum': max_citations,
            'highly_cited_count': highly_cited
        }
    }


def format_report_text(report: Dict[str, Any]) -> str:
    """
    Format report as human-readable text.

    Args:
        report: Report dictionary

    Returns:
        Formatted text string
    """
    lines = []

    lines.append("=" * 70)
    lines.append("TAIJI PUBLICATIONS DATABASE REPORT")
    lines.append("太极出版物数据库报告")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Generated: {report['metadata']['generated']}")
    lines.append(f"Database Version: {report['metadata']['database_version']}")
    lines.append(f"Last Updated: {report['metadata']['database_updated']}")

    # Summary
    lines.append("")
    lines.append("─" * 70)
    lines.append("SUMMARY")
    lines.append("─" * 70)
    summary = report['summary']
    lines.append(f"  Total Entries: {summary['total_entries']}")
    lines.append(f"  Featured Entries: {summary['featured_entries']}")
    lines.append(f"  Total Citations: {summary['total_citations']}")
    lines.append(f"  Recent Papers (last 2 years): {summary['recent_papers']}")

    # Quality
    lines.append("")
    lines.append("─" * 70)
    lines.append("DATA QUALITY")
    lines.append("─" * 70)
    quality = report['quality']
    lines.append(f"  Overall Quality Score: {quality['overall_score']:.1%}")
    lines.append("  Completeness:")
    for field, value in quality['completeness'].items():
        bar = '█' * int(value * 20) + '░' * (20 - int(value * 20))
        lines.append(f"    {field:18s} [{bar}] {value:.0%}")

    # Validation
    validation = report['validation']
    status = "✅ VALID" if validation['is_valid'] else "❌ INVALID"
    lines.append(f"  Validation: {status}")
    lines.append(f"    Errors: {validation['error_count']}")
    lines.append(f"    Warnings: {validation['warning_count']}")

    # Relevance
    lines.append("")
    lines.append("─" * 70)
    lines.append("TAIJI RELEVANCE")
    lines.append("─" * 70)
    relevance = report['relevance']
    lines.append(f"  Average Relevance Score: {relevance['average_score']:.2f}")
    lines.append(f"  High Relevance (≥0.8): {relevance['high_relevance_count']}")
    lines.append(f"  Medium Relevance (0.5-0.8): {relevance['medium_relevance_count']}")
    lines.append(f"  Low Relevance (<0.5): {relevance['low_relevance_count']}")

    # Citations
    lines.append("")
    lines.append("─" * 70)
    lines.append("CITATIONS")
    lines.append("─" * 70)
    citations = report['citations']
    lines.append(f"  Average Citations: {citations['average']:.1f}")
    lines.append(f"  Maximum Citations: {citations['maximum']}")
    lines.append(f"  Highly Cited (≥10): {citations['highly_cited_count']}")

    # Statistics
    lines.append("")
    lines.append("─" * 70)
    lines.append("PUBLICATIONS BY YEAR")
    lines.append("─" * 70)
    for year, count in sorted(report['statistics']['by_year'].items(), reverse=True):
        bar = '█' * min(count * 2, 40)
        lines.append(f"  {year}: {bar} ({count})")

    lines.append("")
    lines.append("─" * 70)
    lines.append("TOP KEYWORDS")
    lines.append("─" * 70)
    for kw, count in list(report['statistics']['top_keywords'].items())[:10]:
        lines.append(f"  {kw}: {count}")

    lines.append("")
    lines.append("=" * 70)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Generate reports for Taiji Publications Database'
    )

    parser.add_argument('--output', '-o', type=Path,
                        help='Output file path (JSON)')
    parser.add_argument('--json', action='store_true',
                        help='Output as JSON to stdout')

    args = parser.parse_args()

    # Load database
    db = load_database(DATABASE_PATH)

    # Generate report
    report = generate_full_report(db)

    # Output
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Report saved to {args.output}")
    elif args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_report_text(report))


if __name__ == '__main__':
    main()
