# Taiji Publications Database Library
# 太极出版物数据库库

"""
This package provides core functionality for the Taiji publications database:

- api_client: API clients for arXiv, Crossref, Semantic Scholar, INSPIRE-HEP
- db_manager: Database loading, saving, and querying
- classifier: Taiji relevance scoring and classification
- validator: Data validation and quality checking
"""

from .db_manager import (
    load_database,
    save_database,
    find_by_doi,
    find_by_arxiv,
    add_entry,
    update_entry,
    generate_entry_id,
)

from .api_client import (
    ArxivClient,
    CrossrefClient,
    SemanticScholarClient,
    InspireClient,
)

from .classifier import (
    TaijiRelevanceScorer,
    suggest_classification,
)

from .validator import (
    validate_entry,
    validate_database,
    find_duplicates,
    ValidationResult,
)

__version__ = "1.0.0"
__all__ = [
    # Database management
    "load_database",
    "save_database",
    "find_by_doi",
    "find_by_arxiv",
    "add_entry",
    "update_entry",
    "generate_entry_id",
    # API clients
    "ArxivClient",
    "CrossrefClient",
    "SemanticScholarClient",
    "InspireClient",
    # Classification
    "TaijiRelevanceScorer",
    "suggest_classification",
    # Validation
    "validate_entry",
    "validate_database",
    "find_duplicates",
    "ValidationResult",
]
