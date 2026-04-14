# CLAUDE.md - Development Context & History

**Project**: Taiji Publications & Talks Portal
**Created**: 2025-04-09
**Last Updated**: 2025-04-14
**Status**: Citation Tracking System Implemented (v3.0.0)

---

## Project Overview

### English Version

The Taiji Publications & Talks Portal is a static website built with Hugo to showcase publications and presentations related to the Taiji space gravitational wave detection project. The site is designed to be community-maintained through GitHub pull requests, with automated validation and deployment.

**Key Objectives:**
- Provide a centralized, searchable repository of Taiji-related publications
- Showcase talks and presentations from conferences, seminars, and public events
- Enable easy community contributions through GitHub workflow
- Maintain high data quality through automated validation
- Present content in an accessible, responsive design
- **Track citations and discover related papers automatically**

**Technology Stack:**
- **Static Site Generator**: Hugo (extended version)
- **Styling**: Custom SCSS with LIGO-inspired minimal academic design
- **Deployment**: GitHub Pages via GitHub Actions
- **Validation**: Python scripts for JSON/YAML schema checking
- **Data Format**: JSON database with Hugo content sync
- **Citation Tracking**: Semantic Scholar, Crossref, arXiv, INSPIRE-HEP APIs
- **Build System**: Makefile-driven development workflow

### 中文版本

太极出版物与报告门户网站是一个使用Hugo构建的静态网站，用于展示与太极空间引力波探测项目相关的出版物和演讲。该网站设计为通过GitHub拉取请求进行社区维护，具有自动验证和部署功能。

**主要目标：**
- 提供太极相关出版物的集中、可搜索存储库
- 展示来自会议、研讨会和公共活动的演讲和报告
- 通过GitHub工作流程实现简便的社区贡献
- 通过自动验证保持高数据质量
- 以可访问、响应式的设计呈现内容
- **自动追踪引用并发现相关论文**

**技术栈：**
- **静态站点生成器**：Hugo（扩展版本）
- **样式**：自定义SCSS，采用LIGO风格的简约学术设计
- **部署**：通过GitHub Actions部署到GitHub Pages
- **验证**：用于JSON/YAML模式检查的Python脚本
- **数据格式**：JSON数据库与Hugo内容同步
- **引用追踪**：Semantic Scholar、Crossref、arXiv、INSPIRE-HEP API
- **构建系统**：Makefile驱动的开发工作流

---

## Architecture Decisions

### Why Hugo?

1. **Performance**: Fast build times even with hundreds of publications
2. **Simplicity**: Single binary, no runtime dependencies
3. **Native Features**: Built-in taxonomies, data file support, RSS generation
4. **GitHub Pages**: Seamless deployment via GitHub Actions
5. **Community**: Large ecosystem and excellent documentation

### Why JSON Database?

1. **Structured Data**: Enforces consistent schema across entries
2. **API Integration**: Easy to populate from external APIs (arXiv, Crossref, etc.)
3. **Citation Tracking**: Supports complex relationships and metadata
4. **Dual Sync**: Database syncs to both Hugo content and data files
5. **Validation**: JSON Schema validation for data quality

### Why Makefile?

1. **Single Entry Point**: All commands through `make`
2. **Dependency Management**: Automatic ordering of tasks
3. **Documentation**: Self-documenting with `make help`
4. **CI/CD Ready**: Easy integration with GitHub Actions
5. **Cross-Platform**: Works on Linux, macOS, and WSL

### Design Philosophy

1. **Simplicity First**: Minimal dependencies, straightforward structure
2. **Academic Presentation**: Clean, LIGO-inspired design focused on content
3. **Community-Driven**: Easy contribution workflow via GitHub
4. **Data Quality**: Automated validation prevents errors
5. **Accessibility**: Responsive design, semantic HTML
6. **Maintainability**: Clear documentation, modular code

---

## File Structure Map

```
TJ_info/
├── .github/
│   ├── workflows/
│   │   ├── hugo-build.yml          # Deploy to GitHub Pages
│   │   └── validate-data.yml       # Validate PRs
│   ├── ISSUE_TEMPLATE/
│   │   ├── add-publication.md      # Publication submission template
│   │   └── add-talk.md             # Talk submission template
│   └── pull_request_template.md    # PR checklist
│
├── archetypes/
│   ├── publications.md             # Template for new publications
│   └── talks.md                    # Template for new talks
│
├── assets/
│   ├── css/
│   │   ├── main.scss               # Main stylesheet
│   │   └── _variables.scss         # Color/spacing variables
│   └── js/
│       └── table-filter.js         # Filtering/sorting logic
│
├── config/                         # [NEW] Configuration files
│   ├── taxonomy.yaml               # Taiji classification system
│   ├── schema.json                 # JSON Schema for validation
│   └── api_keys.yaml.example       # API keys template
│
├── content/
│   ├── publications/
│   │   ├── _index.md               # Publications landing page
│   │   └── [publication files]     # Individual publications
│   ├── talks/
│   │   ├── _index.md               # Talks landing page
│   │   └── [talk files]            # Individual talks
│   └── contribute/
│       └── _index.md               # Contribution guidelines
│
├── data/
│   ├── papers.json                 # [NEW] Main publications database
│   ├── citations_cache.json        # [NEW] Citation relationships
│   └── api_cache/                  # [NEW] API response cache
│       ├── arxiv/
│       ├── crossref/
│       └── semantic_scholar/
│
├── database/                       # [NEW] Export formats
│   ├── papers.bib                  # BibTeX export
│   ├── papers.csv                  # CSV export
│   ├── papers.md                   # Markdown export
│   └── papers.json                 # JSON export
│
├── layouts/
│   ├── _default/
│   │   ├── baseof.html             # Base template
│   │   ├── list.html               # Default list view
│   │   └── single.html             # Default single view
│   ├── publications/
│   │   ├── list.html               # Publications table
│   │   └── single.html             # Publication detail
│   ├── talks/
│   │   ├── list.html               # Talks grouped by type
│   │   └── single.html             # Talk detail
│   ├── partials/
│   │   ├── header.html             # Site header
│   │   ├── footer.html             # Site footer
│   │   └── talk-card.html          # Talk card component
│   └── index.html                  # Homepage
│
├── reports/                        # [NEW] Generated reports
│   └── quality_report.json
│
├── scripts/
│   ├── lib/                        # [NEW] Shared Python libraries
│   │   ├── __init__.py
│   │   ├── api_client.py           # API clients (arXiv, Crossref, S2, INSPIRE)
│   │   ├── db_manager.py           # Database operations
│   │   ├── classifier.py           # Taiji relevance scoring
│   │   └── validator.py            # Data validation
│   │
│   ├── add_paper.py                # [NEW] Add papers by DOI/arXiv
│   ├── find_citations.py           # [NEW] Citation tracking
│   ├── sync_database.py            # [NEW] Sync DB to Hugo
│   ├── export_data.py              # [NEW] Multi-format export
│   ├── validate_data.py            # [NEW] Database validation
│   ├── update_citations.py         # [NEW] Update citation counts
│   ├── generate_report.py          # [NEW] Quality reports
│   ├── validate-publication.py     # Legacy publication validator
│   └── validate-talk.py            # Legacy talk validator
│
├── static/
│   ├── images/                     # Logo, favicon, etc.
│   └── downloads/                  # Static files
│
├── Makefile                        # [NEW] Development commands
├── requirements.txt                # [NEW] Python dependencies
├── hugo.toml                       # Hugo configuration
├── README.md                       # Project documentation
├── CONTRIBUTING.md                 # Contribution guide
└── CLAUDE.md                       # This file
```

---

## Citation Tracking System

### Overview

The citation tracking system allows automatic discovery of papers citing Taiji publications and evaluates their relevance to the project.

### Data Flow

```
External APIs                     Python Scripts                    Output
─────────────                     ──────────────                    ──────
arXiv API ────────┐
                  │
Crossref API ─────┼──→ scripts/lib/api_client.py ──→ data/papers.json
                  │              │
Semantic Scholar ─┤              ├──→ data/citations_cache.json
                  │              │
INSPIRE-HEP ──────┘              └──→ content/publications/*.md
                                              │
                                              ↓
                                     Hugo Static Site
```

### Database Structure (`data/papers.json`)

```json
{
  "metadata": {
    "version": "1.0",
    "project": "Taiji Publications",
    "last_updated": "2025-04-14",
    "total_entries": 5
  },
  "entries": [
    {
      "entry_id": "10.1103/PhysRevD.111.084023",
      "title": "Paper Title",
      "authors": [{"name": "Author", "affiliation": "Institution"}],
      "year": 2025,
      "journal": "Physical Review D",
      "doi": "10.1103/PhysRevD.111.084023",
      "arxiv_id": "2603.25327",
      "keywords": ["keyword1", "keyword2"],
      "publication_type": "journal",
      "featured": true,
      "citation_count": 0,
      "classification": {
        "research_area": "pathfinder",
        "source_types": ["mbhb"],
        "methods": ["simulation"],
        "relevance_score": 1.0
      }
    }
  ]
}
```

### Classification Taxonomy

**Research Areas:**
- `mission_design` - Orbital mechanics, constellation design
- `instrument` - Laser systems, interferometry, drag-free control
- `data_analysis` - Signal processing, parameter estimation
- `source_modeling` - Waveform modeling, source populations
- `science_case` - Astrophysics, cosmology, fundamental physics
- `pathfinder` - Taiji-1, Taiji-2, technology demonstrations

**Source Types:**
- `mbhb` - Massive Black Hole Binaries
- `emri` - Extreme Mass Ratio Inspirals
- `galactic_binary` - Galactic compact binaries
- `sgwb` - Stochastic Gravitational Wave Background
- `verification_binary` - Known calibration sources
- `cosmological` - Standard/dark sirens

**Methods:**
- `data_analysis`, `waveform_modeling`, `parameter_estimation`
- `noise_modeling`, `tdi`, `simulation`

---

## Common Tasks

### Using Makefile Commands

```bash
# Show all available commands
make help

# Install Python dependencies
make install

# Check dependencies
make check-deps
```

### Database Operations

```bash
# Validate database
make validate

# Show statistics
make stats

# Generate quality report
make report
```

### Adding Papers

```bash
# Add by DOI
make add-doi DOI=10.1103/PhysRevD.100.022003

# Add by arXiv ID
make add-arxiv ID=2401.12345

# Interactive mode
make add-interactive
```

### Citation Tracking

```bash
# Find citations for a paper
make find-citations ARXIV=2401.12345

# Auto-add relevant citations
make find-citations-auto ARXIV=2401.12345 LIMIT=10 MIN_REL=0.5

# Dry run (no changes)
make find-citations-dry ARXIV=2401.12345

# Update all citation counts
make update-citations
```

### Export and Sync

```bash
# Export to all formats (BibTeX, CSV, Markdown, JSON)
make export

# Export specific format
make export-bibtex
make export-csv

# Sync database to Hugo content
make sync
```

### Hugo Site

```bash
# Start development server
make serve

# Build for production
make build

# Full deployment workflow
make deploy
```

### View the Site Locally

```bash
# Start development server
hugo server -D

# Visit http://localhost:1313
# Press Ctrl+C to stop
```

---

## Key Implementation Details

### Publications Page

**Features:**
- Sortable table with columns: Date, Title, Authors, Journal, Links
- Client-side filtering by year, type, and search term
- arXiv and DOI badges with direct links
- Responsive table design (horizontal scroll on mobile)
- **Citation count display**
- **Taiji relevance scoring**

**Data Structure:**
```yaml
title: "Publication Title"
date: YYYY-MM-DD
authors:
  - name: "Author Name"
    affiliation: "Institution"
journal: "Journal Name"
volume: "123"
pages: "456-789"
year: 2025
arxiv: "2503.12345"
doi: "10.1103/PhysRevD.123.456789"
keywords: ["keyword1", "keyword2"]
publication_type: "journal"  # journal, conference, preprint
featured: false
citation_count: 42
```

### Talks Page

**Features:**
- Grouped by talk type (conference, seminar, workshop, colloquium, public)
- Card-based layout with speaker info and event details
- Links to slides and video recordings
- Filterable by year and keywords

**Data Structure:**
```yaml
title: "Talk Title"
date: YYYY-MM-DD
speaker:
  name: "Speaker Name"
  affiliation: "Institution"
event: "Event Name"
location: "City, Country"
talk_type: "conference"
slides_url: "https://..."
video_url: "https://..."
keywords: ["keyword1", "keyword2"]
```

### Styling

**Color Scheme (LIGO-inspired Academic Style):**
- Background: #ffffff (white)
- Text: #000000 (black)
- Links: #000080 (navy blue)
- Table Headers: LightSteelBlue
- Table Alternating Rows: Lavender
- Borders: #000080 (navy, 2px solid)
- Hover: #f0f0f0 (light grey)

**Typography:**
- Font: Arial, Helvetica, sans-serif
- Base Size: 10pt
- Line Height: 1.4

**Responsive Breakpoints:**
- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

### Validation

**Database Validation (via `make validate`):**
- Required fields: entry_id, title, authors, year
- Valid publication types: journal, conference, preprint, thesis, report
- DOI format validation (10.xxxx/...)
- arXiv ID format validation (YYMM.NNNNN)
- Duplicate detection (DOI, arXiv, title similarity)
- Classification validity

**Legacy Validation:**
- `scripts/validate-publication.py` - Hugo frontmatter validation
- `scripts/validate-talk.py` - Talk frontmatter validation

---

## LIGO-Style Design Reference

The site follows the LIGO Papers page design philosophy:

**Style Reference Link:**
- LIGO Papers page: [https://pnp.ligo.org/ppcomm/Papers.html](https://pnp.ligo.org/ppcomm/Papers.html)

**Visual Characteristics:**
- White background throughout
- Navy blue (#000080) for links and borders
- Light steel blue table headers
- Lavender alternating table rows
- 10pt Arial/Helvetica font
- 2px solid navy borders on tables
- No gradients, shadows, or decorative elements
- Minimal spacing and padding

**Functional Features:**
- Sortable table columns (click headers)
- DOI toggle button (show/hide DOI links)
- Year and type filtering
- Search functionality
- Simple, clean presentation

---

## Modification History

### 2025-04-14: Citation Tracking System (v3.0.0)

**Major Feature Addition:**
- Complete citation tracking system inspired by Survey4GWML
- External API integration (arXiv, Crossref, Semantic Scholar, INSPIRE-HEP)
- JSON database system with Hugo content sync
- Makefile-driven development workflow

**New Files Created:**

| File | Lines | Purpose |
|------|-------|---------|
| `Makefile` | ~180 | Development command center |
| `requirements.txt` | ~12 | Python dependencies |
| `config/taxonomy.yaml` | ~150 | Taiji classification system |
| `config/schema.json` | ~200 | JSON Schema validation |
| `config/api_keys.yaml.example` | ~25 | API keys template |
| `data/papers.json` | dynamic | Main publications database |
| `data/citations_cache.json` | dynamic | Citation relationships |
| `scripts/lib/__init__.py` | ~50 | Package exports |
| `scripts/lib/api_client.py` | ~650 | API clients |
| `scripts/lib/db_manager.py` | ~350 | Database operations |
| `scripts/lib/classifier.py` | ~280 | Relevance scoring |
| `scripts/lib/validator.py` | ~550 | Data validation |
| `scripts/add_paper.py` | ~300 | Add papers CLI |
| `scripts/find_citations.py` | ~400 | Citation tracking |
| `scripts/sync_database.py` | ~200 | Hugo sync |
| `scripts/export_data.py` | ~250 | Multi-format export |
| `scripts/validate_data.py` | ~200 | Validation CLI |
| `scripts/update_citations.py` | ~150 | Citation updates |
| `scripts/generate_report.py` | ~250 | Report generation |

**Key Features:**
- Add papers via DOI or arXiv ID with automatic metadata fetch
- Track citations using Semantic Scholar API
- Score papers for Taiji relevance automatically
- Export to BibTeX, CSV, Markdown, JSON
- Sync database to Hugo content
- Quality reports and statistics

### 2025-04-09: LIGO-Style Redesign (v2.0.0)

**Major Design Overhaul:**
- Completely redesigned to match LIGO Papers page aesthetic
- Removed all red color branding (#8c0000)
- Implemented minimal, academic presentation style

### 2025-04-09: Initial Implementation (v1.0.0)

**Created:**
- Hugo site structure with custom theme
- Publications and talks content types
- Responsive layouts with Taiji branding
- JavaScript filtering and sorting
- GitHub Actions workflows
- Python validation scripts
- Comprehensive documentation

---

## Future Enhancements

### Completed (v3.0.0)

- [x] BibTeX Export
- [x] Citation tracking
- [x] Statistics/Quality reports
- [x] Multi-format export (CSV, JSON, Markdown)
- [x] Integration with INSPIRE-HEP

### Short-term (Next 3 months)

1. **Search Functionality**
   - Full-text search across publications and talks
   - Implement with Lunr.js or similar

2. **Automated arXiv Monitoring**
   - Monitor arXiv for Taiji-related papers
   - GitHub Action for automatic PR creation

3. **Enhanced Filtering**
   - Multi-select keyword filtering
   - Author search and filtering
   - Date range selection

### Medium-term (3-6 months)

1. **RSS Feeds**
   - Per-category RSS feeds
   - New publications feed

2. **ORCID Integration**
   - Link authors to ORCID profiles
   - Import publication data from ORCID

3. **Multi-language Support**
   - Chinese translation of interface
   - Bilingual content support

### Long-term (6+ months)

1. **API Endpoint**
   - JSON API for programmatic access
   - GraphQL interface

2. **Interactive Visualizations**
   - Timeline of publications
   - Topic evolution over time
   - Citation network graph

---

## Troubleshooting

### Common Issues

**Make command not found:**
```bash
# Install make (macOS)
xcode-select --install

# Install make (Ubuntu/Debian)
sudo apt-get install build-essential
```

**Python dependencies missing:**
```bash
make install
# or
pip install -r requirements.txt
```

**API rate limiting:**
- Use caching (data/api_cache/)
- Add delay between requests
- Get API key for Semantic Scholar

**Database validation fails:**
```bash
make validate
# Check specific issues
python scripts/validate_data.py --check format
python scripts/validate_data.py --check duplicates
```

**Hugo build fails:**
- Check Hugo version (requires extended version)
- Verify YAML frontmatter syntax
- Run `make sync` to regenerate content

### Debug Commands

```bash
# Check dependencies
make check-deps

# Check Hugo version
hugo version

# Validate database with details
python scripts/validate_data.py --json

# Test API clients
python scripts/lib/api_client.py --arxiv 2401.12345

# Show database stats
make stats
```

---

## Development Guidelines

### Code Style

**Python:**
- Follow PEP 8
- Use type hints
- Add docstrings to all functions
- Handle API errors gracefully

**SCSS:**
- Use variables for colors and spacing
- Follow BEM naming convention
- Mobile-first media queries

**JavaScript:**
- Use vanilla JS (no frameworks)
- Add comments for complex logic
- Handle edge cases gracefully

### Git Workflow

**Branches:**
- `main`: Production branch
- `feature/*`: New features
- `fix/*`: Bug fixes
- `docs/*`: Documentation updates

**Commits:**
- Use conventional commit format
- Clear, descriptive messages
- Reference issues when applicable

---

## Contact & Support

**Maintainers:**
- GitHub: [@taiji-publications](https://github.com/taiji-publications)

**Resources:**
- Hugo Documentation: https://gohugo.io/documentation/
- GitHub Pages: https://pages.github.com/
- Taiji Mission: https://ictp-ap.org/
- Semantic Scholar API: https://api.semanticscholar.org/

**Community:**
- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: Questions and general discussion
- Pull Requests: Code and content contributions

---

## Acknowledgments

This portal was developed for the Taiji Collaboration and is hosted by ICTP-AP (International Centre for Theoretical Physics Asia-Pacific).

**Special Thanks:**
- Taiji Collaboration members for content contributions
- ICTP-AP for hosting and support
- Hugo community for excellent documentation
- GitHub for free hosting via GitHub Pages
- Survey4GWML project for architecture inspiration

---

**Last Updated**: 2025-04-14
**Version**: 3.0.0
**Status**: Production Ready (Citation Tracking System)
