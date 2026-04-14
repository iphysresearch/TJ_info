#!/usr/bin/env python3
"""
Data Validator for Taiji Publications Database
太极出版物数据库验证器

Provides functions for:
- Validating individual entries against schema
- Validating the entire database
- Finding duplicates
- Checking data quality
"""

import json
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

try:
    from jsonschema import validate, ValidationError as JsonSchemaValidationError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

try:
    from Levenshtein import ratio as levenshtein_ratio
    HAS_LEVENSHTEIN = True
except ImportError:
    HAS_LEVENSHTEIN = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default paths
DEFAULT_DATABASE_PATH = Path("data/papers.json")
DEFAULT_SCHEMA_PATH = Path("config/schema.json")


# ═══════════════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════════════

class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """A single validation issue."""
    severity: ValidationSeverity
    field: str
    message: str
    entry_id: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of validation check."""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    checked_entries: int = 0
    error_count: int = 0
    warning_count: int = 0

    def add_issue(self, issue: ValidationIssue):
        """Add an issue to the result."""
        self.issues.append(issue)
        if issue.severity == ValidationSeverity.ERROR:
            self.error_count += 1
            self.is_valid = False
        elif issue.severity == ValidationSeverity.WARNING:
            self.warning_count += 1

    def merge(self, other: 'ValidationResult'):
        """Merge another validation result into this one."""
        self.issues.extend(other.issues)
        self.error_count += other.error_count
        self.warning_count += other.warning_count
        if not other.is_valid:
            self.is_valid = False


# ═══════════════════════════════════════════════════════════════════════════════
# Schema Loading
# ═══════════════════════════════════════════════════════════════════════════════

def load_schema(path: Path = DEFAULT_SCHEMA_PATH) -> Optional[Dict[str, Any]]:
    """
    Load JSON schema for validation.

    Args:
        path: Path to schema file

    Returns:
        Schema dictionary or None if not found
    """
    if not path.exists():
        logger.warning(f"Schema file not found: {path}")
        return None

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading schema: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# Entry Validation
# ═══════════════════════════════════════════════════════════════════════════════

def validate_entry(entry: Dict[str, Any], schema: Optional[Dict] = None) -> ValidationResult:
    """
    Validate a single paper entry.

    Args:
        entry: Entry dictionary to validate
        schema: JSON schema (optional, uses builtin rules if not provided)

    Returns:
        ValidationResult with any issues found
    """
    result = ValidationResult(is_valid=True, checked_entries=1)
    entry_id = entry.get('entry_id', 'unknown')

    # ─────────────────────────────────────────────────────────────────────────
    # Required fields
    # ─────────────────────────────────────────────────────────────────────────
    required_fields = ['entry_id', 'title', 'authors', 'year']
    for field in required_fields:
        if field not in entry:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                field=field,
                message=f"Missing required field: {field}",
                entry_id=entry_id
            ))
        elif not entry[field]:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                field=field,
                message=f"Required field is empty: {field}",
                entry_id=entry_id
            ))

    # ─────────────────────────────────────────────────────────────────────────
    # Title validation
    # ─────────────────────────────────────────────────────────────────────────
    title = entry.get('title', '')
    if title:
        if len(title) < 10:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                field='title',
                message="Title seems too short",
                entry_id=entry_id
            ))
        if len(title) > 500:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                field='title',
                message="Title seems too long",
                entry_id=entry_id
            ))

    # ─────────────────────────────────────────────────────────────────────────
    # Authors validation
    # ─────────────────────────────────────────────────────────────────────────
    authors = entry.get('authors', [])
    if authors:
        if not isinstance(authors, list):
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                field='authors',
                message="Authors must be a list",
                entry_id=entry_id
            ))
        else:
            for i, author in enumerate(authors):
                if not isinstance(author, dict):
                    result.add_issue(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        field=f'authors[{i}]',
                        message="Each author must be a dictionary",
                        entry_id=entry_id
                    ))
                elif 'name' not in author or not author['name']:
                    result.add_issue(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        field=f'authors[{i}].name',
                        message="Author name is required",
                        entry_id=entry_id
                    ))

    # ─────────────────────────────────────────────────────────────────────────
    # Year validation
    # ─────────────────────────────────────────────────────────────────────────
    year = entry.get('year')
    if year is not None:
        try:
            year = int(year)
            current_year = datetime.now().year
            if year < 1900 or year > current_year + 1:
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field='year',
                    message=f"Year {year} seems invalid (expected 1900-{current_year + 1})",
                    entry_id=entry_id
                ))
        except (ValueError, TypeError):
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                field='year',
                message="Year must be an integer",
                entry_id=entry_id
            ))

    # ─────────────────────────────────────────────────────────────────────────
    # DOI validation
    # ─────────────────────────────────────────────────────────────────────────
    doi = entry.get('doi')
    if doi:
        # DOI should match pattern 10.XXXX/XXXXX
        doi_pattern = r'^10\.\d{4,}/.+'
        if not re.match(doi_pattern, doi):
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                field='doi',
                message=f"DOI format may be invalid: {doi}",
                entry_id=entry_id,
                suggestion="DOI should start with '10.' followed by publisher prefix"
            ))

    # ─────────────────────────────────────────────────────────────────────────
    # arXiv ID validation
    # ─────────────────────────────────────────────────────────────────────────
    arxiv_id = entry.get('arxiv_id')
    if arxiv_id:
        # Modern arXiv ID format: YYMM.NNNNN or YYMM.NNNNNvN
        arxiv_pattern = r'^\d{4}\.\d{4,5}(v\d+)?$'
        if not re.match(arxiv_pattern, arxiv_id):
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                field='arxiv_id',
                message=f"arXiv ID format may be invalid: {arxiv_id}",
                entry_id=entry_id,
                suggestion="Expected format: YYMM.NNNNN (e.g., 2401.12345)"
            ))

    # ─────────────────────────────────────────────────────────────────────────
    # Keywords validation
    # ─────────────────────────────────────────────────────────────────────────
    keywords = entry.get('keywords', [])
    if keywords:
        if not isinstance(keywords, list):
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                field='keywords',
                message="Keywords must be a list",
                entry_id=entry_id
            ))
        elif len(keywords) == 0:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.INFO,
                field='keywords',
                message="No keywords provided",
                entry_id=entry_id,
                suggestion="Consider adding keywords for better discoverability"
            ))

    # ─────────────────────────────────────────────────────────────────────────
    # Publication type validation
    # ─────────────────────────────────────────────────────────────────────────
    pub_type = entry.get('publication_type')
    valid_types = ['journal', 'conference', 'preprint', 'thesis', 'report']
    if pub_type and pub_type not in valid_types:
        result.add_issue(ValidationIssue(
            severity=ValidationSeverity.WARNING,
            field='publication_type',
            message=f"Unknown publication type: {pub_type}",
            entry_id=entry_id,
            suggestion=f"Valid types: {', '.join(valid_types)}"
        ))

    # ─────────────────────────────────────────────────────────────────────────
    # Classification validation
    # ─────────────────────────────────────────────────────────────────────────
    classification = entry.get('classification', {})
    if classification:
        valid_areas = ['mission_design', 'instrument', 'data_analysis',
                       'source_modeling', 'science_case', 'pathfinder']
        area = classification.get('research_area')
        if area and area not in valid_areas:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                field='classification.research_area',
                message=f"Unknown research area: {area}",
                entry_id=entry_id,
                suggestion=f"Valid areas: {', '.join(valid_areas)}"
            ))

        relevance = classification.get('relevance_score')
        if relevance is not None:
            try:
                relevance = float(relevance)
                if relevance < 0 or relevance > 1:
                    result.add_issue(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        field='classification.relevance_score',
                        message=f"Relevance score out of range: {relevance}",
                        entry_id=entry_id,
                        suggestion="Score should be between 0 and 1"
                    ))
            except (ValueError, TypeError):
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field='classification.relevance_score',
                    message="Relevance score must be a number",
                    entry_id=entry_id
                ))

    # ─────────────────────────────────────────────────────────────────────────
    # JSON Schema validation (if available)
    # ─────────────────────────────────────────────────────────────────────────
    # NOTE: JSON Schema validation with $ref is complex; we rely on manual validation
    # above for better error messages. Keeping this code for future enhancement
    # when using a proper JSON Schema resolver.
    # if schema and HAS_JSONSCHEMA:
    #     try:
    #         # Would need proper $ref resolution
    #         pass
    #     except JsonSchemaValidationError as e:
    #         pass

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Database Validation
# ═══════════════════════════════════════════════════════════════════════════════

def validate_database(db: Dict[str, Any],
                      schema_path: Path = DEFAULT_SCHEMA_PATH) -> ValidationResult:
    """
    Validate the entire database.

    Args:
        db: Database dictionary
        schema_path: Path to JSON schema file

    Returns:
        ValidationResult with all issues found
    """
    result = ValidationResult(is_valid=True)
    schema = load_schema(schema_path)

    # Validate metadata
    metadata = db.get('metadata', {})
    if not metadata:
        result.add_issue(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            field='metadata',
            message="Database metadata is missing"
        ))
    else:
        if 'version' not in metadata:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                field='metadata.version',
                message="Database version is not specified"
            ))

    # Validate entries
    entries = db.get('entries', [])
    if not entries:
        result.add_issue(ValidationIssue(
            severity=ValidationSeverity.INFO,
            field='entries',
            message="Database has no entries"
        ))

    for entry in entries:
        entry_result = validate_entry(entry, schema)
        result.merge(entry_result)
        result.checked_entries += 1

    # Check for duplicates
    duplicate_result = find_duplicates(db)
    result.merge(duplicate_result)

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Duplicate Detection
# ═══════════════════════════════════════════════════════════════════════════════

def find_duplicates(db: Dict[str, Any], similarity_threshold: float = 0.9) -> ValidationResult:
    """
    Find duplicate entries in the database.

    Checks for:
    - Exact DOI matches
    - Exact arXiv ID matches
    - Similar titles

    Args:
        db: Database dictionary
        similarity_threshold: Threshold for title similarity (0-1)

    Returns:
        ValidationResult with duplicate issues
    """
    result = ValidationResult(is_valid=True)
    entries = db.get('entries', [])

    # Index by DOI
    doi_index = {}
    for entry in entries:
        doi = entry.get('doi')
        if doi:
            doi_lower = doi.lower()
            if doi_lower in doi_index:
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field='doi',
                    message=f"Duplicate DOI: {doi}",
                    entry_id=entry.get('entry_id'),
                    suggestion=f"Also found in: {doi_index[doi_lower]}"
                ))
            else:
                doi_index[doi_lower] = entry.get('entry_id')

    # Index by arXiv ID
    arxiv_index = {}
    for entry in entries:
        arxiv_id = entry.get('arxiv_id')
        if arxiv_id:
            # Normalize: remove version number
            arxiv_clean = arxiv_id.split('v')[0].lower()
            if arxiv_clean in arxiv_index:
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field='arxiv_id',
                    message=f"Duplicate arXiv ID: {arxiv_id}",
                    entry_id=entry.get('entry_id'),
                    suggestion=f"Also found in: {arxiv_index[arxiv_clean]}"
                ))
            else:
                arxiv_index[arxiv_clean] = entry.get('entry_id')

    # Check title similarity (O(n^2) but okay for small databases)
    if HAS_LEVENSHTEIN and len(entries) < 1000:
        titles = [(i, e.get('title', '').lower(), e.get('entry_id'))
                  for i, e in enumerate(entries)]

        checked_pairs = set()
        for i, (idx1, title1, id1) in enumerate(titles):
            for idx2, title2, id2 in titles[i+1:]:
                if (id1, id2) in checked_pairs or (id2, id1) in checked_pairs:
                    continue

                similarity = levenshtein_ratio(title1, title2)
                if similarity >= similarity_threshold:
                    result.add_issue(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        field='title',
                        message=f"Similar titles ({similarity:.0%}): '{entries[idx1].get('title')}'",
                        entry_id=id1,
                        suggestion=f"Similar to: {id2}"
                    ))
                    checked_pairs.add((id1, id2))

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Quality Checks
# ═══════════════════════════════════════════════════════════════════════════════

def check_quality(db: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check data quality metrics.

    Args:
        db: Database dictionary

    Returns:
        Dictionary with quality metrics
    """
    entries = db.get('entries', [])
    total = len(entries)

    if total == 0:
        return {
            'total_entries': 0,
            'completeness': {},
            'quality_score': 0.0
        }

    # Completeness metrics
    has_doi = sum(1 for e in entries if e.get('doi'))
    has_arxiv = sum(1 for e in entries if e.get('arxiv_id'))
    has_abstract = sum(1 for e in entries if e.get('abstract'))
    has_keywords = sum(1 for e in entries if e.get('keywords'))
    has_classification = sum(1 for e in entries if e.get('classification'))
    has_citations = sum(1 for e in entries if e.get('citations', {}).get('count', 0) > 0)

    completeness = {
        'doi': has_doi / total,
        'arxiv_id': has_arxiv / total,
        'abstract': has_abstract / total,
        'keywords': has_keywords / total,
        'classification': has_classification / total,
        'citations': has_citations / total
    }

    # Overall quality score (weighted average)
    weights = {
        'doi': 0.2,
        'arxiv_id': 0.1,
        'abstract': 0.25,
        'keywords': 0.15,
        'classification': 0.15,
        'citations': 0.15
    }

    quality_score = sum(
        completeness[field] * weight
        for field, weight in weights.items()
    )

    # Entry-level quality
    entry_scores = []
    for entry in entries:
        score = entry.get('metadata', {}).get('quality_score')
        if score is not None:
            entry_scores.append(score)

    avg_entry_score = sum(entry_scores) / len(entry_scores) if entry_scores else None

    return {
        'total_entries': total,
        'completeness': {k: round(v, 3) for k, v in completeness.items()},
        'quality_score': round(quality_score, 3),
        'avg_entry_quality': round(avg_entry_score, 3) if avg_entry_score else None,
        'issues': {
            'missing_doi': total - has_doi,
            'missing_abstract': total - has_abstract,
            'missing_keywords': total - has_keywords,
            'missing_classification': total - has_classification
        }
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Citation Validation
# ═══════════════════════════════════════════════════════════════════════════════

def validate_citations(db: Dict[str, Any]) -> ValidationResult:
    """
    Validate citation data in the database.

    Args:
        db: Database dictionary

    Returns:
        ValidationResult with citation issues
    """
    result = ValidationResult(is_valid=True)
    entries = db.get('entries', [])
    today = datetime.now().strftime('%Y-%m-%d')

    for entry in entries:
        entry_id = entry.get('entry_id', 'unknown')
        citations = entry.get('citations', {})

        if not citations:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.INFO,
                field='citations',
                message="No citation data",
                entry_id=entry_id,
                suggestion="Run 'make update-citations' to fetch citation counts"
            ))
            continue

        # Check citation count
        count = citations.get('count')
        if count is not None and count < 0:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                field='citations.count',
                message=f"Invalid citation count: {count}",
                entry_id=entry_id
            ))

        # Check last_updated date
        last_updated = citations.get('last_updated')
        if last_updated:
            try:
                updated_date = datetime.strptime(last_updated, '%Y-%m-%d')
                days_old = (datetime.now() - updated_date).days
                if days_old > 30:
                    result.add_issue(ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        field='citations.last_updated',
                        message=f"Citation data is {days_old} days old",
                        entry_id=entry_id,
                        suggestion="Consider updating with 'make update-citations'"
                    ))
            except ValueError:
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field='citations.last_updated',
                    message=f"Invalid date format: {last_updated}",
                    entry_id=entry_id,
                    suggestion="Expected format: YYYY-MM-DD"
                ))

        # Check source
        valid_sources = ['semantic_scholar', 'crossref', 'inspire', 'ads', 'manual']
        source = citations.get('source')
        if source and source not in valid_sources:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                field='citations.source',
                message=f"Unknown citation source: {source}",
                entry_id=entry_id,
                suggestion=f"Valid sources: {', '.join(valid_sources)}"
            ))

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════════════════

def generate_validation_report(result: ValidationResult) -> str:
    """
    Generate a human-readable validation report.

    Args:
        result: ValidationResult to report

    Returns:
        Formatted report string
    """
    lines = []
    lines.append("=" * 60)
    lines.append("VALIDATION REPORT")
    lines.append("=" * 60)
    lines.append("")

    # Summary
    status = "✅ VALID" if result.is_valid else "❌ INVALID"
    lines.append(f"Status: {status}")
    lines.append(f"Entries checked: {result.checked_entries}")
    lines.append(f"Errors: {result.error_count}")
    lines.append(f"Warnings: {result.warning_count}")
    lines.append("")

    # Group issues by severity
    errors = [i for i in result.issues if i.severity == ValidationSeverity.ERROR]
    warnings = [i for i in result.issues if i.severity == ValidationSeverity.WARNING]
    infos = [i for i in result.issues if i.severity == ValidationSeverity.INFO]

    if errors:
        lines.append("─" * 60)
        lines.append("ERRORS:")
        lines.append("─" * 60)
        for issue in errors:
            lines.append(f"  [{issue.entry_id or 'database'}] {issue.field}")
            lines.append(f"    {issue.message}")
            if issue.suggestion:
                lines.append(f"    → {issue.suggestion}")
        lines.append("")

    if warnings:
        lines.append("─" * 60)
        lines.append("WARNINGS:")
        lines.append("─" * 60)
        for issue in warnings:
            lines.append(f"  [{issue.entry_id or 'database'}] {issue.field}")
            lines.append(f"    {issue.message}")
            if issue.suggestion:
                lines.append(f"    → {issue.suggestion}")
        lines.append("")

    if infos:
        lines.append("─" * 60)
        lines.append("INFO:")
        lines.append("─" * 60)
        for issue in infos[:10]:  # Limit info messages
            lines.append(f"  [{issue.entry_id or 'database'}] {issue.message}")
        if len(infos) > 10:
            lines.append(f"  ... and {len(infos) - 10} more")
        lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI for testing
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Validate Taiji publications database')
    parser.add_argument('--database', default=str(DEFAULT_DATABASE_PATH),
                        help='Path to database file')
    parser.add_argument('--schema', default=str(DEFAULT_SCHEMA_PATH),
                        help='Path to schema file')
    parser.add_argument('--check', choices=['all', 'format', 'duplicates', 'citations', 'quality'],
                        default='all', help='Type of check to run')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    # Load database
    db_path = Path(args.database)
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        exit(1)

    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)

    # Run checks
    if args.check == 'all':
        result = validate_database(db, Path(args.schema))
    elif args.check == 'format':
        result = ValidationResult(is_valid=True)
        for entry in db.get('entries', []):
            result.merge(validate_entry(entry))
    elif args.check == 'duplicates':
        result = find_duplicates(db)
    elif args.check == 'citations':
        result = validate_citations(db)
    elif args.check == 'quality':
        quality = check_quality(db)
        if args.json:
            print(json.dumps(quality, indent=2))
        else:
            print("Quality Report:")
            print(f"  Total entries: {quality['total_entries']}")
            print(f"  Quality score: {quality['quality_score']:.1%}")
            print("\n  Completeness:")
            for field, value in quality['completeness'].items():
                print(f"    {field}: {value:.1%}")
        exit(0)

    # Output
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

    exit(0 if result.is_valid else 1)
