#!/usr/bin/env python3
"""
Taiji Relevance Classifier
太极相关性分类器

Provides functions for:
- Computing Taiji relevance scores for papers
- Suggesting classifications based on keywords and content
- Mapping keywords to taxonomy categories
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default taxonomy path
DEFAULT_TAXONOMY_PATH = Path("config/taxonomy.yaml")


# ═══════════════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ClassificationResult:
    """Result of paper classification."""
    research_area: Optional[str]
    research_area_score: float
    source_types: List[str]
    methods: List[str]
    relevance_score: float
    explanation: str
    matched_keywords: List[str]


# ═══════════════════════════════════════════════════════════════════════════════
# Taxonomy Loading
# ═══════════════════════════════════════════════════════════════════════════════

def load_taxonomy(path: Path = DEFAULT_TAXONOMY_PATH) -> Dict[str, Any]:
    """
    Load the taxonomy configuration.

    Args:
        path: Path to taxonomy YAML file

    Returns:
        Taxonomy dictionary
    """
    if not path.exists():
        logger.warning(f"Taxonomy file not found: {path}")
        return get_default_taxonomy()

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading taxonomy: {e}")
        return get_default_taxonomy()


def get_default_taxonomy() -> Dict[str, Any]:
    """Return default taxonomy if file not found."""
    return {
        "research_areas": {
            "mission_design": {"keywords": ["mission", "constellation", "orbit"]},
            "instrument": {"keywords": ["laser", "interferometry", "accelerometer"]},
            "data_analysis": {"keywords": ["data analysis", "signal processing"]},
            "source_modeling": {"keywords": ["waveform", "template"]},
            "science_case": {"keywords": ["cosmology", "astrophysics"]},
            "pathfinder": {"keywords": ["pathfinder", "Taiji-1", "Taiji-2"]}
        },
        "source_types": {
            "mbhb": {"keywords": ["massive black hole", "MBH", "MBHB"]},
            "emri": {"keywords": ["EMRI", "extreme mass ratio"]},
            "galactic_binary": {"keywords": ["galactic binary", "white dwarf"]},
            "sgwb": {"keywords": ["stochastic", "background"]},
            "verification_binary": {"keywords": ["verification"]},
            "cosmological": {"keywords": ["cosmology", "Hubble"]}
        },
        "methods": {
            "data_analysis": {"keywords": ["data analysis"]},
            "waveform_modeling": {"keywords": ["waveform"]},
            "parameter_estimation": {"keywords": ["parameter estimation", "PE"]},
            "noise_modeling": {"keywords": ["noise", "PSD"]},
            "tdi": {"keywords": ["TDI", "time-delay interferometry"]},
            "simulation": {"keywords": ["simulation", "mock data"]}
        },
        "taiji_relevance_keywords": {
            "high_relevance": ["Taiji", "太极", "LISA-Taiji"],
            "medium_relevance": ["space-based gravitational wave", "millihertz", "LISA", "TianQin"],
            "low_relevance": ["gravitational wave"]
        }
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Taiji Relevance Scorer
# ═══════════════════════════════════════════════════════════════════════════════

class TaijiRelevanceScorer:
    """
    Compute relevance scores for papers related to Taiji project.
    计算论文与太极项目的相关性评分
    """

    def __init__(self, taxonomy_path: Path = DEFAULT_TAXONOMY_PATH):
        self.taxonomy = load_taxonomy(taxonomy_path)
        self._build_keyword_indices()

    def _build_keyword_indices(self):
        """Build keyword lookup indices for efficient matching."""
        # Relevance keywords
        relevance = self.taxonomy.get('taiji_relevance_keywords', {})
        self.high_relevance_keywords = [
            kw.lower() for kw in relevance.get('high_relevance', [])
        ]
        self.medium_relevance_keywords = [
            kw.lower() for kw in relevance.get('medium_relevance', [])
        ]
        self.low_relevance_keywords = [
            kw.lower() for kw in relevance.get('low_relevance', [])
        ]

        # Research area keywords
        self.area_keywords = {}
        for area, config in self.taxonomy.get('research_areas', {}).items():
            keywords = config.get('keywords', []) if isinstance(config, dict) else []
            self.area_keywords[area] = [kw.lower() for kw in keywords]

        # Source type keywords
        self.source_keywords = {}
        for source, config in self.taxonomy.get('source_types', {}).items():
            keywords = config.get('keywords', []) if isinstance(config, dict) else []
            self.source_keywords[source] = [kw.lower() for kw in keywords]

        # Method keywords
        self.method_keywords = {}
        for method, config in self.taxonomy.get('methods', {}).items():
            keywords = config.get('keywords', []) if isinstance(config, dict) else []
            self.method_keywords[method] = [kw.lower() for kw in keywords]

    def _text_contains_keyword(self, text: str, keyword: str) -> bool:
        """Check if text contains keyword (case-insensitive, word boundary aware)."""
        # Use word boundary for short keywords to avoid false matches
        if len(keyword) <= 3:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            return bool(re.search(pattern, text, re.IGNORECASE))
        return keyword.lower() in text.lower()

    def compute_relevance_score(self, title: str, abstract: str = "",
                                 keywords: List[str] = None) -> Tuple[float, List[str], str]:
        """
        Compute Taiji relevance score for a paper.

        Args:
            title: Paper title
            abstract: Paper abstract
            keywords: Paper keywords

        Returns:
            Tuple of (score, matched_keywords, explanation)
        """
        keywords = keywords or []

        # Combine all text for matching
        text = f"{title} {abstract} {' '.join(keywords)}".lower()
        matched = []
        score = 0.0
        reasons = []

        # Check high relevance keywords (score: 0.8-1.0)
        for kw in self.high_relevance_keywords:
            if self._text_contains_keyword(text, kw):
                matched.append(kw)
                score = max(score, 1.0)
                reasons.append(f"High relevance: contains '{kw}'")

        # Check medium relevance keywords (score: 0.5-0.7)
        if score < 1.0:
            for kw in self.medium_relevance_keywords:
                if self._text_contains_keyword(text, kw):
                    matched.append(kw)
                    score = max(score, 0.7)
                    reasons.append(f"Medium relevance: contains '{kw}'")

        # Check low relevance keywords (score: 0.2-0.4)
        if score < 0.5:
            for kw in self.low_relevance_keywords:
                if self._text_contains_keyword(text, kw):
                    matched.append(kw)
                    score = max(score, 0.3)
                    reasons.append(f"Low relevance: contains '{kw}'")

        # Boost score based on specific mentions
        if 'taiji' in text.lower() or '太极' in text:
            score = min(1.0, score + 0.2)
            if 'taiji' not in [m.lower() for m in matched]:
                matched.append('Taiji')

        explanation = "; ".join(reasons) if reasons else "No Taiji-related keywords found"

        return (round(score, 2), matched, explanation)

    def score_paper(self, paper: Dict[str, Any]) -> float:
        """
        Compute relevance score for a paper dictionary.

        Args:
            paper: Paper dictionary with 'title', 'abstract', 'keywords' fields

        Returns:
            Relevance score (0-1)
        """
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')
        keywords = paper.get('keywords', [])

        score, _, _ = self.compute_relevance_score(title, abstract, keywords)
        return score


# ═══════════════════════════════════════════════════════════════════════════════
# Classification Suggester
# ═══════════════════════════════════════════════════════════════════════════════

def suggest_classification(title: str, abstract: str = "",
                           keywords: List[str] = None,
                           taxonomy_path: Path = DEFAULT_TAXONOMY_PATH) -> ClassificationResult:
    """
    Suggest classification for a paper based on content analysis.

    Args:
        title: Paper title
        abstract: Paper abstract
        keywords: Paper keywords
        taxonomy_path: Path to taxonomy file

    Returns:
        ClassificationResult with suggested categories
    """
    taxonomy = load_taxonomy(taxonomy_path)
    keywords = keywords or []

    # Combine text for matching
    text = f"{title} {abstract} {' '.join(keywords)}".lower()
    matched_keywords = []

    # Detect research area
    area_scores = {}
    for area, config in taxonomy.get('research_areas', {}).items():
        area_keywords = config.get('keywords', []) if isinstance(config, dict) else []
        count = 0
        for kw in area_keywords:
            if kw.lower() in text:
                count += 1
                matched_keywords.append(kw)
        if count > 0:
            area_scores[area] = count

    # Best research area
    if area_scores:
        research_area = max(area_scores, key=area_scores.get)
        research_area_score = min(1.0, area_scores[research_area] / 3)
    else:
        research_area = None
        research_area_score = 0.0

    # Detect source types
    source_types = []
    for source, config in taxonomy.get('source_types', {}).items():
        source_keywords = config.get('keywords', []) if isinstance(config, dict) else []
        for kw in source_keywords:
            if kw.lower() in text:
                if source not in source_types:
                    source_types.append(source)
                    matched_keywords.append(kw)
                break

    # Detect methods
    methods = []
    for method, config in taxonomy.get('methods', {}).items():
        method_keywords = config.get('keywords', []) if isinstance(config, dict) else []
        for kw in method_keywords:
            if kw.lower() in text:
                if method not in methods:
                    methods.append(method)
                    matched_keywords.append(kw)
                break

    # Compute overall relevance score
    scorer = TaijiRelevanceScorer(taxonomy_path)
    relevance_score, relevance_matched, explanation = scorer.compute_relevance_score(
        title, abstract, keywords
    )
    matched_keywords.extend(relevance_matched)

    # Remove duplicates while preserving order
    seen = set()
    unique_matched = []
    for kw in matched_keywords:
        kw_lower = kw.lower()
        if kw_lower not in seen:
            seen.add(kw_lower)
            unique_matched.append(kw)

    return ClassificationResult(
        research_area=research_area,
        research_area_score=research_area_score,
        source_types=source_types,
        methods=methods,
        relevance_score=relevance_score,
        explanation=explanation,
        matched_keywords=unique_matched
    )


def classify_paper(paper: Dict[str, Any],
                   taxonomy_path: Path = DEFAULT_TAXONOMY_PATH) -> Dict[str, Any]:
    """
    Classify a paper and return classification dictionary.

    Args:
        paper: Paper dictionary
        taxonomy_path: Path to taxonomy file

    Returns:
        Classification dictionary suitable for paper entry
    """
    title = paper.get('title', '')
    abstract = paper.get('abstract', '')
    keywords = paper.get('keywords', [])

    result = suggest_classification(title, abstract, keywords, taxonomy_path)

    return {
        'research_area': result.research_area,
        'source_types': result.source_types,
        'methods': result.methods,
        'relevance_score': result.relevance_score
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Batch Classification
# ═══════════════════════════════════════════════════════════════════════════════

def classify_papers(papers: List[Dict[str, Any]],
                    min_relevance: float = 0.0,
                    taxonomy_path: Path = DEFAULT_TAXONOMY_PATH) -> List[Tuple[Dict[str, Any], ClassificationResult]]:
    """
    Classify multiple papers and filter by relevance.

    Args:
        papers: List of paper dictionaries
        min_relevance: Minimum relevance score to include
        taxonomy_path: Path to taxonomy file

    Returns:
        List of (paper, classification) tuples, sorted by relevance
    """
    results = []

    for paper in papers:
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')
        keywords = paper.get('keywords', [])

        classification = suggest_classification(title, abstract, keywords, taxonomy_path)

        if classification.relevance_score >= min_relevance:
            results.append((paper, classification))

    # Sort by relevance score descending
    results.sort(key=lambda x: x[1].relevance_score, reverse=True)

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# CLI for testing
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Classify papers for Taiji relevance')
    parser.add_argument('--title', required=True, help='Paper title')
    parser.add_argument('--abstract', default='', help='Paper abstract')
    parser.add_argument('--keywords', nargs='*', default=[], help='Paper keywords')
    parser.add_argument('--taxonomy', default=str(DEFAULT_TAXONOMY_PATH), help='Taxonomy file path')

    args = parser.parse_args()

    result = suggest_classification(
        args.title,
        args.abstract,
        args.keywords,
        Path(args.taxonomy)
    )

    print(f"Title: {args.title}")
    print(f"\nClassification Results:")
    print(f"  Research Area: {result.research_area} (score: {result.research_area_score:.2f})")
    print(f"  Source Types: {', '.join(result.source_types) or 'None'}")
    print(f"  Methods: {', '.join(result.methods) or 'None'}")
    print(f"  Relevance Score: {result.relevance_score:.2f}")
    print(f"  Explanation: {result.explanation}")
    print(f"  Matched Keywords: {', '.join(result.matched_keywords) or 'None'}")
