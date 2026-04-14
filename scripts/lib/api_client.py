#!/usr/bin/env python3
"""
API Clients for External Services
外部服务 API 客户端

Provides unified interfaces for:
- arXiv API: Paper metadata retrieval
- Crossref API: DOI resolution and journal information
- Semantic Scholar API: Citation tracking
- INSPIRE-HEP API: High-energy physics literature
"""

import os
import json
import time
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

import requests
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Base Classes
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class APIResponse:
    """Standardized API response wrapper."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    source: str = ""
    cached: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class BaseAPIClient(ABC):
    """Base class for all API clients."""

    def __init__(self, cache_dir: Optional[Path] = None, cache_ttl_hours: int = 24):
        self.cache_dir = cache_dir
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TaijiPublications/1.0 (https://github.com/taiji-publications)'
        })

    def _get_cache_path(self, key: str) -> Path:
        """Generate cache file path for a given key."""
        if not self.cache_dir:
            return None
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{hash_key}.json"

    def _read_cache(self, key: str) -> Optional[Dict]:
        """Read from cache if valid."""
        cache_path = self._get_cache_path(key)
        if not cache_path or not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)

            # Check TTL
            cached_time = datetime.fromisoformat(cached.get('timestamp', '2000-01-01'))
            if datetime.now() - cached_time > self.cache_ttl:
                return None

            return cached.get('data')
        except (json.JSONDecodeError, KeyError):
            return None

    def _write_cache(self, key: str, data: Dict):
        """Write to cache."""
        cache_path = self._get_cache_path(key)
        if not cache_path:
            return

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'data': data
            }, f, indent=2, ensure_ascii=False)

    def _make_request(self, url: str, params: Dict = None,
                      headers: Dict = None, method: str = 'GET') -> requests.Response:
        """Make HTTP request with error handling."""
        try:
            if method == 'GET':
                response = self.session.get(url, params=params, headers=headers, timeout=30)
            elif method == 'POST':
                response = self.session.post(url, json=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    @abstractmethod
    def get_paper(self, identifier: str) -> APIResponse:
        """Get paper metadata by identifier."""
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# arXiv API Client
# ═══════════════════════════════════════════════════════════════════════════════

class ArxivClient(BaseAPIClient):
    """arXiv API client for paper metadata retrieval."""

    BASE_URL = "http://export.arxiv.org/api/query"
    RATE_LIMIT_SECONDS = 3  # arXiv recommends 1 request per 3 seconds

    def __init__(self, cache_dir: Optional[Path] = None):
        super().__init__(cache_dir or Path("data/api_cache/arxiv"))
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_SECONDS:
            time.sleep(self.RATE_LIMIT_SECONDS - elapsed)
        self.last_request_time = time.time()

    def _parse_entry(self, entry: ET.Element, ns: Dict[str, str]) -> Dict[str, Any]:
        """Parse a single arXiv entry from XML."""
        def get_text(tag: str, namespace: str = 'atom') -> Optional[str]:
            elem = entry.find(f"{ns[namespace]}{tag}")
            return elem.text.strip() if elem is not None and elem.text else None

        # Extract arXiv ID from the id URL
        id_url = get_text('id')
        arxiv_id = id_url.split('/abs/')[-1] if id_url else None

        # Extract authors
        authors = []
        for author in entry.findall(f"{ns['atom']}author"):
            name = author.find(f"{ns['atom']}name")
            affiliation = author.find(f"{ns['arxiv']}affiliation")
            authors.append({
                'name': name.text.strip() if name is not None and name.text else None,
                'affiliation': affiliation.text.strip() if affiliation is not None and affiliation.text else None
            })

        # Extract categories
        categories = [
            cat.get('term') for cat in entry.findall(f"{ns['atom']}category")
        ]

        # Extract DOI if present
        doi = None
        for link in entry.findall(f"{ns['atom']}link"):
            if link.get('title') == 'doi':
                doi = link.get('href', '').replace('http://dx.doi.org/', '')

        # Also check arxiv:doi element
        doi_elem = entry.find(f"{ns['arxiv']}doi")
        if doi_elem is not None and doi_elem.text:
            doi = doi_elem.text.strip()

        # Extract journal reference
        journal_ref = entry.find(f"{ns['arxiv']}journal_ref")

        # Extract published and updated dates
        published = get_text('published')
        updated = get_text('updated')

        return {
            'arxiv_id': arxiv_id,
            'title': get_text('title'),
            'abstract': get_text('summary'),
            'authors': [a for a in authors if a.get('name')],
            'categories': categories,
            'primary_category': entry.find(f"{ns['arxiv']}primary_category").get('term') if entry.find(f"{ns['arxiv']}primary_category") is not None else None,
            'doi': doi,
            'journal_ref': journal_ref.text.strip() if journal_ref is not None and journal_ref.text else None,
            'published': published,
            'updated': updated,
            'url': f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None
        }

    def get_paper(self, arxiv_id: str) -> APIResponse:
        """
        Get paper metadata by arXiv ID.

        Args:
            arxiv_id: arXiv identifier (e.g., "2401.12345" or "2401.12345v1")

        Returns:
            APIResponse with paper metadata
        """
        # Normalize arXiv ID (remove version if present for caching)
        clean_id = arxiv_id.split('v')[0] if 'v' in arxiv_id else arxiv_id
        cache_key = f"arxiv_{clean_id}"

        # Check cache
        cached = self._read_cache(cache_key)
        if cached:
            logger.info(f"Cache hit for arXiv:{arxiv_id}")
            return APIResponse(success=True, data=cached, source='arxiv', cached=True)

        # Rate limit
        self._rate_limit()

        try:
            params = {
                'id_list': arxiv_id,
                'max_results': 1
            }
            response = self._make_request(self.BASE_URL, params=params)

            # Parse XML
            root = ET.fromstring(response.content)
            ns = {
                'atom': '{http://www.w3.org/2005/Atom}',
                'arxiv': '{http://arxiv.org/schemas/atom}',
                'opensearch': '{http://a9.com/-/spec/opensearch/1.1/}'
            }

            # Find entry
            entry = root.find(f"{ns['atom']}entry")
            if entry is None:
                return APIResponse(
                    success=False,
                    error=f"No paper found for arXiv:{arxiv_id}",
                    source='arxiv'
                )

            data = self._parse_entry(entry, ns)

            # Cache result
            self._write_cache(cache_key, data)

            return APIResponse(success=True, data=data, source='arxiv')

        except Exception as e:
            logger.error(f"arXiv API error: {e}")
            return APIResponse(success=False, error=str(e), source='arxiv')

    def search(self, query: str, max_results: int = 10,
               start: int = 0) -> APIResponse:
        """
        Search arXiv for papers.

        Args:
            query: Search query (supports arXiv search syntax)
            max_results: Maximum number of results
            start: Starting index for pagination

        Returns:
            APIResponse with list of papers
        """
        self._rate_limit()

        try:
            params = {
                'search_query': query,
                'max_results': max_results,
                'start': start,
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }
            response = self._make_request(self.BASE_URL, params=params)

            root = ET.fromstring(response.content)
            ns = {
                'atom': '{http://www.w3.org/2005/Atom}',
                'arxiv': '{http://arxiv.org/schemas/atom}',
                'opensearch': '{http://a9.com/-/spec/opensearch/1.1/}'
            }

            papers = []
            for entry in root.findall(f"{ns['atom']}entry"):
                papers.append(self._parse_entry(entry, ns))

            # Get total results
            total_elem = root.find(f"{ns['opensearch']}totalResults")
            total = int(total_elem.text) if total_elem is not None else len(papers)

            return APIResponse(
                success=True,
                data={'papers': papers, 'total': total, 'start': start},
                source='arxiv'
            )

        except Exception as e:
            logger.error(f"arXiv search error: {e}")
            return APIResponse(success=False, error=str(e), source='arxiv')


# ═══════════════════════════════════════════════════════════════════════════════
# Crossref API Client
# ═══════════════════════════════════════════════════════════════════════════════

class CrossrefClient(BaseAPIClient):
    """Crossref API client for DOI resolution and journal information."""

    BASE_URL = "https://api.crossref.org"

    def __init__(self, cache_dir: Optional[Path] = None, email: Optional[str] = None):
        super().__init__(cache_dir or Path("data/api_cache/crossref"))
        # Add email for polite pool
        if email:
            self.session.headers.update({'mailto': email})

    def get_paper(self, doi: str) -> APIResponse:
        """
        Get paper metadata by DOI.

        Args:
            doi: Digital Object Identifier (e.g., "10.1103/PhysRevD.100.022003")

        Returns:
            APIResponse with paper metadata
        """
        # Normalize DOI
        if doi.startswith('https://doi.org/'):
            doi = doi[16:]
        elif doi.startswith('http://dx.doi.org/'):
            doi = doi[18:]

        cache_key = f"crossref_{doi.replace('/', '_')}"

        # Check cache
        cached = self._read_cache(cache_key)
        if cached:
            logger.info(f"Cache hit for DOI:{doi}")
            return APIResponse(success=True, data=cached, source='crossref', cached=True)

        try:
            url = f"{self.BASE_URL}/works/{doi}"
            response = self._make_request(url)
            result = response.json()

            if result.get('status') != 'ok':
                return APIResponse(
                    success=False,
                    error=f"Crossref API error: {result.get('message', 'Unknown error')}",
                    source='crossref'
                )

            message = result.get('message', {})

            # Parse authors
            authors = []
            for author in message.get('author', []):
                name_parts = []
                if author.get('given'):
                    name_parts.append(author['given'])
                if author.get('family'):
                    name_parts.append(author['family'])

                affiliations = author.get('affiliation', [])
                affiliation = affiliations[0].get('name') if affiliations else None

                authors.append({
                    'name': ' '.join(name_parts),
                    'affiliation': affiliation,
                    'orcid': author.get('ORCID')
                })

            # Parse date
            date_parts = message.get('published', {}).get('date-parts', [[]])
            if date_parts and date_parts[0]:
                year = date_parts[0][0] if len(date_parts[0]) > 0 else None
                month = date_parts[0][1] if len(date_parts[0]) > 1 else 1
                day = date_parts[0][2] if len(date_parts[0]) > 2 else 1
            else:
                year, month, day = None, 1, 1

            data = {
                'doi': doi,
                'title': message.get('title', [''])[0],
                'authors': authors,
                'year': year,
                'journal': message.get('container-title', [''])[0],
                'volume': message.get('volume'),
                'issue': message.get('issue'),
                'pages': message.get('page'),
                'publisher': message.get('publisher'),
                'type': message.get('type'),
                'url': message.get('URL'),
                'abstract': message.get('abstract'),
                'subject': message.get('subject', []),
                'reference_count': message.get('reference-count', 0),
                'is_referenced_by_count': message.get('is-referenced-by-count', 0),
                'published_date': f"{year}-{month:02d}-{day:02d}" if year else None
            }

            # Cache result
            self._write_cache(cache_key, data)

            return APIResponse(success=True, data=data, source='crossref')

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return APIResponse(
                    success=False,
                    error=f"DOI not found: {doi}",
                    source='crossref'
                )
            raise
        except Exception as e:
            logger.error(f"Crossref API error: {e}")
            return APIResponse(success=False, error=str(e), source='crossref')


# ═══════════════════════════════════════════════════════════════════════════════
# Semantic Scholar API Client
# ═══════════════════════════════════════════════════════════════════════════════

class SemanticScholarClient(BaseAPIClient):
    """Semantic Scholar API client for citation tracking."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    RATE_LIMIT_SECONDS = 1  # 100 requests per 5 minutes without key

    def __init__(self, cache_dir: Optional[Path] = None, api_key: Optional[str] = None):
        super().__init__(cache_dir or Path("data/api_cache/semantic_scholar"))
        self.api_key = api_key
        if api_key:
            self.session.headers.update({'x-api-key': api_key})
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_SECONDS:
            time.sleep(self.RATE_LIMIT_SECONDS - elapsed)
        self.last_request_time = time.time()

    def get_paper(self, identifier: str, id_type: str = 'arxiv') -> APIResponse:
        """
        Get paper metadata by identifier.

        Args:
            identifier: Paper identifier
            id_type: Type of identifier ('arxiv', 'doi', 'ss' for Semantic Scholar ID)

        Returns:
            APIResponse with paper metadata
        """
        if id_type == 'arxiv':
            paper_id = f"ARXIV:{identifier}"
        elif id_type == 'doi':
            paper_id = f"DOI:{identifier}"
        else:
            paper_id = identifier

        cache_key = f"s2_{id_type}_{identifier.replace('/', '_')}"

        # Check cache
        cached = self._read_cache(cache_key)
        if cached:
            logger.info(f"Cache hit for {id_type}:{identifier}")
            return APIResponse(success=True, data=cached, source='semantic_scholar', cached=True)

        self._rate_limit()

        try:
            url = f"{self.BASE_URL}/paper/{paper_id}"
            params = {
                'fields': 'paperId,title,abstract,year,venue,authors,citationCount,referenceCount,citations,references,externalIds,publicationDate'
            }
            response = self._make_request(url, params=params)
            data = response.json()

            # Transform to standard format
            result = {
                'semantic_scholar_id': data.get('paperId'),
                'title': data.get('title'),
                'abstract': data.get('abstract'),
                'year': data.get('year'),
                'venue': data.get('venue'),
                'authors': [
                    {'name': a.get('name'), 'author_id': a.get('authorId')}
                    for a in data.get('authors', [])
                ],
                'citation_count': data.get('citationCount', 0),
                'reference_count': data.get('referenceCount', 0),
                'external_ids': data.get('externalIds', {}),
                'published_date': data.get('publicationDate')
            }

            # Cache result
            self._write_cache(cache_key, result)

            return APIResponse(success=True, data=result, source='semantic_scholar')

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return APIResponse(
                    success=False,
                    error=f"Paper not found: {identifier}",
                    source='semantic_scholar'
                )
            raise
        except Exception as e:
            logger.error(f"Semantic Scholar API error: {e}")
            return APIResponse(success=False, error=str(e), source='semantic_scholar')

    def get_citations(self, identifier: str, id_type: str = 'arxiv',
                      limit: int = 100, offset: int = 0) -> APIResponse:
        """
        Get papers that cite the given paper.

        Args:
            identifier: Paper identifier
            id_type: Type of identifier ('arxiv', 'doi', 'ss')
            limit: Maximum number of citations to return
            offset: Starting index for pagination

        Returns:
            APIResponse with list of citing papers
        """
        if id_type == 'arxiv':
            paper_id = f"ARXIV:{identifier}"
        elif id_type == 'doi':
            paper_id = f"DOI:{identifier}"
        else:
            paper_id = identifier

        cache_key = f"s2_citations_{id_type}_{identifier.replace('/', '_')}_{offset}_{limit}"

        # Check cache (shorter TTL for citations)
        cached = self._read_cache(cache_key)
        if cached:
            logger.info(f"Cache hit for citations of {id_type}:{identifier}")
            return APIResponse(success=True, data=cached, source='semantic_scholar', cached=True)

        self._rate_limit()

        try:
            url = f"{self.BASE_URL}/paper/{paper_id}/citations"
            params = {
                'fields': 'paperId,title,abstract,year,venue,authors,citationCount,externalIds,publicationDate',
                'limit': limit,
                'offset': offset
            }
            response = self._make_request(url, params=params)
            data = response.json()

            citations = []
            for item in data.get('data', []):
                citing_paper = item.get('citingPaper', {})
                citations.append({
                    'semantic_scholar_id': citing_paper.get('paperId'),
                    'title': citing_paper.get('title'),
                    'abstract': citing_paper.get('abstract'),
                    'year': citing_paper.get('year'),
                    'venue': citing_paper.get('venue'),
                    'authors': [
                        {'name': a.get('name'), 'author_id': a.get('authorId')}
                        for a in citing_paper.get('authors', [])
                    ],
                    'citation_count': citing_paper.get('citationCount', 0),
                    'external_ids': citing_paper.get('externalIds', {}),
                    'published_date': citing_paper.get('publicationDate')
                })

            result = {
                'citations': citations,
                'total': len(citations),  # S2 doesn't provide total count in this endpoint
                'offset': offset
            }

            # Cache result
            self._write_cache(cache_key, result)

            return APIResponse(success=True, data=result, source='semantic_scholar')

        except Exception as e:
            logger.error(f"Semantic Scholar citations error: {e}")
            return APIResponse(success=False, error=str(e), source='semantic_scholar')

    def get_references(self, identifier: str, id_type: str = 'arxiv',
                       limit: int = 100, offset: int = 0) -> APIResponse:
        """
        Get papers referenced by the given paper.

        Args:
            identifier: Paper identifier
            id_type: Type of identifier ('arxiv', 'doi', 'ss')
            limit: Maximum number of references to return
            offset: Starting index for pagination

        Returns:
            APIResponse with list of referenced papers
        """
        if id_type == 'arxiv':
            paper_id = f"ARXIV:{identifier}"
        elif id_type == 'doi':
            paper_id = f"DOI:{identifier}"
        else:
            paper_id = identifier

        self._rate_limit()

        try:
            url = f"{self.BASE_URL}/paper/{paper_id}/references"
            params = {
                'fields': 'paperId,title,abstract,year,venue,authors,citationCount,externalIds',
                'limit': limit,
                'offset': offset
            }
            response = self._make_request(url, params=params)
            data = response.json()

            references = []
            for item in data.get('data', []):
                ref_paper = item.get('citedPaper', {})
                if ref_paper:  # Some references might not be in S2
                    references.append({
                        'semantic_scholar_id': ref_paper.get('paperId'),
                        'title': ref_paper.get('title'),
                        'abstract': ref_paper.get('abstract'),
                        'year': ref_paper.get('year'),
                        'venue': ref_paper.get('venue'),
                        'authors': [
                            {'name': a.get('name'), 'author_id': a.get('authorId')}
                            for a in ref_paper.get('authors', [])
                        ],
                        'citation_count': ref_paper.get('citationCount', 0),
                        'external_ids': ref_paper.get('externalIds', {})
                    })

            return APIResponse(
                success=True,
                data={'references': references, 'total': len(references), 'offset': offset},
                source='semantic_scholar'
            )

        except Exception as e:
            logger.error(f"Semantic Scholar references error: {e}")
            return APIResponse(success=False, error=str(e), source='semantic_scholar')


# ═══════════════════════════════════════════════════════════════════════════════
# INSPIRE-HEP API Client
# ═══════════════════════════════════════════════════════════════════════════════

class InspireClient(BaseAPIClient):
    """INSPIRE-HEP API client for high-energy physics literature."""

    BASE_URL = "https://inspirehep.net/api"

    def __init__(self, cache_dir: Optional[Path] = None):
        super().__init__(cache_dir or Path("data/api_cache/inspire"))

    def get_paper(self, identifier: str, id_type: str = 'arxiv') -> APIResponse:
        """
        Get paper metadata from INSPIRE-HEP.

        Args:
            identifier: Paper identifier
            id_type: Type of identifier ('arxiv', 'doi', 'inspire')

        Returns:
            APIResponse with paper metadata
        """
        cache_key = f"inspire_{id_type}_{identifier.replace('/', '_')}"

        # Check cache
        cached = self._read_cache(cache_key)
        if cached:
            logger.info(f"Cache hit for {id_type}:{identifier}")
            return APIResponse(success=True, data=cached, source='inspire', cached=True)

        try:
            if id_type == 'arxiv':
                url = f"{self.BASE_URL}/arxiv/{identifier}"
            elif id_type == 'doi':
                url = f"{self.BASE_URL}/doi/{identifier}"
            else:
                url = f"{self.BASE_URL}/literature/{identifier}"

            response = self._make_request(url)
            data = response.json()

            metadata = data.get('metadata', {})

            # Parse authors
            authors = []
            for author in metadata.get('authors', []):
                authors.append({
                    'name': author.get('full_name'),
                    'affiliation': author.get('affiliations', [{}])[0].get('value') if author.get('affiliations') else None,
                    'orcid': author.get('ids', [{}])[0].get('value') if author.get('ids') else None
                })

            # Get external IDs
            arxiv_id = None
            doi = None
            for eprint in metadata.get('arxiv_eprints', []):
                arxiv_id = eprint.get('value')
                break
            for doi_obj in metadata.get('dois', []):
                doi = doi_obj.get('value')
                break

            result = {
                'inspire_id': data.get('id'),
                'title': metadata.get('titles', [{}])[0].get('title'),
                'abstract': metadata.get('abstracts', [{}])[0].get('value') if metadata.get('abstracts') else None,
                'authors': authors,
                'year': metadata.get('earliest_date', '')[:4] if metadata.get('earliest_date') else None,
                'arxiv_id': arxiv_id,
                'doi': doi,
                'journal': metadata.get('publication_info', [{}])[0].get('journal_title') if metadata.get('publication_info') else None,
                'volume': metadata.get('publication_info', [{}])[0].get('journal_volume') if metadata.get('publication_info') else None,
                'pages': metadata.get('publication_info', [{}])[0].get('page_start') if metadata.get('publication_info') else None,
                'citation_count': metadata.get('citation_count', 0),
                'keywords': [k.get('value') for k in metadata.get('keywords', []) if k.get('value')]
            }

            # Cache result
            self._write_cache(cache_key, result)

            return APIResponse(success=True, data=result, source='inspire')

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return APIResponse(
                    success=False,
                    error=f"Paper not found in INSPIRE: {identifier}",
                    source='inspire'
                )
            raise
        except Exception as e:
            logger.error(f"INSPIRE API error: {e}")
            return APIResponse(success=False, error=str(e), source='inspire')

    def search(self, query: str, size: int = 10, page: int = 1) -> APIResponse:
        """
        Search INSPIRE-HEP for papers.

        Args:
            query: Search query
            size: Number of results per page
            page: Page number

        Returns:
            APIResponse with list of papers
        """
        try:
            url = f"{self.BASE_URL}/literature"
            params = {
                'q': query,
                'size': size,
                'page': page,
                'sort': 'mostrecent'
            }
            response = self._make_request(url, params=params)
            data = response.json()

            papers = []
            for hit in data.get('hits', {}).get('hits', []):
                metadata = hit.get('metadata', {})
                papers.append({
                    'inspire_id': hit.get('id'),
                    'title': metadata.get('titles', [{}])[0].get('title'),
                    'year': metadata.get('earliest_date', '')[:4] if metadata.get('earliest_date') else None,
                    'citation_count': metadata.get('citation_count', 0)
                })

            return APIResponse(
                success=True,
                data={
                    'papers': papers,
                    'total': data.get('hits', {}).get('total', 0),
                    'page': page
                },
                source='inspire'
            )

        except Exception as e:
            logger.error(f"INSPIRE search error: {e}")
            return APIResponse(success=False, error=str(e), source='inspire')


# ═══════════════════════════════════════════════════════════════════════════════
# Unified Paper Fetcher
# ═══════════════════════════════════════════════════════════════════════════════

class PaperFetcher:
    """Unified interface to fetch paper metadata from multiple sources."""

    def __init__(self, cache_base_dir: Path = Path("data/api_cache")):
        self.arxiv = ArxivClient(cache_base_dir / "arxiv")
        self.crossref = CrossrefClient(cache_base_dir / "crossref")
        self.semantic_scholar = SemanticScholarClient(cache_base_dir / "semantic_scholar")
        self.inspire = InspireClient(cache_base_dir / "inspire")

    def fetch_by_arxiv(self, arxiv_id: str) -> Dict[str, Any]:
        """
        Fetch paper metadata using arXiv ID, combining data from multiple sources.

        Args:
            arxiv_id: arXiv identifier

        Returns:
            Combined metadata dictionary
        """
        result = {
            'arxiv_id': arxiv_id,
            'data_sources': []
        }

        # Try arXiv first (authoritative for preprints)
        arxiv_response = self.arxiv.get_paper(arxiv_id)
        if arxiv_response.success:
            result.update(arxiv_response.data)
            result['data_sources'].append('arxiv')

        # Try to get DOI from arXiv data, then query Crossref
        doi = result.get('doi')
        if doi:
            crossref_response = self.crossref.get_paper(doi)
            if crossref_response.success:
                # Merge Crossref data (prefer Crossref for journal info)
                cr_data = crossref_response.data
                result['journal'] = cr_data.get('journal') or result.get('journal')
                result['volume'] = cr_data.get('volume') or result.get('volume')
                result['pages'] = cr_data.get('pages') or result.get('pages')
                result['publisher'] = cr_data.get('publisher')
                result['data_sources'].append('crossref')

        # Get citation count from Semantic Scholar
        s2_response = self.semantic_scholar.get_paper(arxiv_id, id_type='arxiv')
        if s2_response.success:
            result['citation_count'] = s2_response.data.get('citation_count', 0)
            result['semantic_scholar_id'] = s2_response.data.get('semantic_scholar_id')
            result['data_sources'].append('semantic_scholar')

        return result

    def fetch_by_doi(self, doi: str) -> Dict[str, Any]:
        """
        Fetch paper metadata using DOI, combining data from multiple sources.

        Args:
            doi: Digital Object Identifier

        Returns:
            Combined metadata dictionary
        """
        result = {
            'doi': doi,
            'data_sources': []
        }

        # Try Crossref first (authoritative for DOIs)
        crossref_response = self.crossref.get_paper(doi)
        if crossref_response.success:
            result.update(crossref_response.data)
            result['data_sources'].append('crossref')

        # Get citation count from Semantic Scholar
        s2_response = self.semantic_scholar.get_paper(doi, id_type='doi')
        if s2_response.success:
            result['citation_count'] = s2_response.data.get('citation_count', 0)
            result['semantic_scholar_id'] = s2_response.data.get('semantic_scholar_id')
            result['data_sources'].append('semantic_scholar')

            # Get arXiv ID if available
            external_ids = s2_response.data.get('external_ids', {})
            if external_ids.get('ArXiv'):
                result['arxiv_id'] = external_ids['ArXiv']

        return result


# ═══════════════════════════════════════════════════════════════════════════════
# CLI for testing
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Test API clients')
    parser.add_argument('--arxiv', help='Fetch by arXiv ID')
    parser.add_argument('--doi', help='Fetch by DOI')
    parser.add_argument('--search', help='Search arXiv')
    parser.add_argument('--citations', help='Get citations for arXiv ID')

    args = parser.parse_args()

    fetcher = PaperFetcher()

    if args.arxiv:
        result = fetcher.fetch_by_arxiv(args.arxiv)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.doi:
        result = fetcher.fetch_by_doi(args.doi)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.search:
        response = fetcher.arxiv.search(args.search)
        if response.success:
            print(json.dumps(response.data, indent=2, ensure_ascii=False))
        else:
            print(f"Error: {response.error}")

    elif args.citations:
        response = fetcher.semantic_scholar.get_citations(args.citations)
        if response.success:
            print(json.dumps(response.data, indent=2, ensure_ascii=False))
        else:
            print(f"Error: {response.error}")

    else:
        parser.print_help()
