#!/usr/bin/env python3
"""
Validate Taiji Publications Database
验证太极出版物数据库

Usage:
    python scripts/validate_data.py
    python scripts/validate_data.py --check format
    python scripts/validate_data.py --check duplicates
    python scripts/validate_data.py --stats
"""

import sys
import json
import argparse
import logging
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.db_manager import load_database, get_statistics
from lib.validator import (
    validate_database, validate_entry, find_duplicates,
    validate_citations, check_quality,
    generate_validation_report, ValidationResult
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
DATABASE_PATH = Path("data/papers.json")
SCHEMA_PATH = Path("config/schema.json")


def display_statistics(db: dict):
    """Display database statistics."""
    stats = get_statistics(db)

    print("\n" + "=" * 60)
    print("DATABASE STATISTICS")
    print("=" * 60)

    print(f"\n📊 Overview")
    print(f"   Total entries: {stats['total_entries']}")
    print(f"   Featured: {stats['featured_count']}")
    print(f"   Total citations: {stats['total_citations']}")

    print(f"\n📅 By Year")
    for year, count in sorted(stats['years'].items(), reverse=True):
        bar = '█' * min(count * 2, 40)
        print(f"   {year}: {bar} ({count})")

    print(f"\n📁 Publication Types")
    for ptype, count in stats['publication_types'].items():
        print(f"   {ptype}: {count}")

    print(f"\n🔬 Research Areas")
    for area, count in stats.get('research_areas', {}).items():
        print(f"   {area}: {count}")

    print(f"\n🏷️ Top Keywords")
    for keyword, count in list(stats['top_keywords'].items())[:10]:
        print(f"   {keyword}: {count}")

    print(f"\n✅ Completeness")
    print(f"   With DOI: {stats['entries_with_doi']}/{stats['total_entries']}")
    print(f"   With arXiv: {stats['entries_with_arxiv']}/{stats['total_entries']}")
    print(f"   With abstract: {stats['entries_with_abstract']}/{stats['total_entries']}")


def display_quality(db: dict):
    """Display data quality metrics."""
    quality = check_quality(db)

    print("\n" + "=" * 60)
    print("DATA QUALITY REPORT")
    print("=" * 60)

    print(f"\n📊 Overall Quality Score: {quality['quality_score']:.1%}")

    if quality.get('avg_entry_quality'):
        print(f"   Average Entry Quality: {quality['avg_entry_quality']:.1%}")

    print(f"\n📋 Completeness Metrics")
    for field, value in quality['completeness'].items():
        bar_width = int(value * 20)
        bar = '█' * bar_width + '░' * (20 - bar_width)
        print(f"   {field:20s} [{bar}] {value:.0%}")

    print(f"\n⚠️ Missing Data")
    for issue, count in quality['issues'].items():
        if count > 0:
            print(f"   {issue}: {count} entries")


def main():
    parser = argparse.ArgumentParser(
        description='Validate Taiji Publications Database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/validate_data.py
    python scripts/validate_data.py --check format
    python scripts/validate_data.py --check duplicates
    python scripts/validate_data.py --check citations
    python scripts/validate_data.py --stats
    python scripts/validate_data.py --quality
        """
    )

    parser.add_argument('--check', choices=['all', 'format', 'duplicates', 'citations'],
                        default='all', help='Type of check to run')
    parser.add_argument('--stats', action='store_true',
                        help='Show database statistics')
    parser.add_argument('--quality', action='store_true',
                        help='Show data quality report')
    parser.add_argument('--json', action='store_true',
                        help='Output as JSON')

    args = parser.parse_args()

    # Load database
    if not DATABASE_PATH.exists():
        print(f"❌ Database not found: {DATABASE_PATH}")
        sys.exit(1)

    db = load_database(DATABASE_PATH)

    # Statistics mode
    if args.stats:
        if args.json:
            stats = get_statistics(db)
            print(json.dumps(stats, indent=2))
        else:
            display_statistics(db)
        sys.exit(0)

    # Quality mode
    if args.quality:
        if args.json:
            quality = check_quality(db)
            print(json.dumps(quality, indent=2))
        else:
            display_quality(db)
        sys.exit(0)

    # Validation mode
    print("\n" + "=" * 60)
    print("VALIDATING DATABASE")
    print("=" * 60 + "\n")

    if args.check == 'all':
        result = validate_database(db, SCHEMA_PATH)
    elif args.check == 'format':
        result = ValidationResult(is_valid=True)
        for entry in db.get('entries', []):
            result.merge(validate_entry(entry))
            result.checked_entries += 1
    elif args.check == 'duplicates':
        result = find_duplicates(db)
    elif args.check == 'citations':
        result = validate_citations(db)

    # Output results
    if args.json:
        output = {
            'is_valid': result.is_valid,
            'checked_entries': result.checked_entries,
            'error_count': result.error_count,
            'warning_count': result.warning_count,
            'issues': [
                {
                    'severity': i.severity.value,
                    'field': i.field,
                    'message': i.message,
                    'entry_id': i.entry_id,
                    'suggestion': i.suggestion
                }
                for i in result.issues
            ]
        }
        print(json.dumps(output, indent=2))
    else:
        print(generate_validation_report(result))

    # Exit code based on validation result
    sys.exit(0 if result.is_valid else 1)


if __name__ == '__main__':
    main()
