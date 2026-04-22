# Taiji Publications & Talks Portal

A static website showcasing publications and talks related to the Taiji space gravitational wave detection project. Built with Hugo and hosted on GitHub Pages.

## Overview

This portal provides a comprehensive, searchable collection of:
- **Publications**: Peer-reviewed papers, preprints, and conference proceedings
- **Talks**: Conference presentations, seminars, workshops, and public lectures

## Features

- **LIGO-style publication table** with sorting and filtering
- **Responsive design** optimized for mobile and desktop
- **Easy contribution workflow** via GitHub pull requests
- **Automated validation** of submitted content
- **BibTeX/CSV/JSON export** functionality
- **Citation tracking** via Semantic Scholar API
- **Multi-band search** across titles, authors, and keywords
- **Taiji relevance scoring** for automatic classification
- **Institution database** for Taiji Alliance member organizations

## Quick Start

### Viewing the Site

Visit the live site at: [https://taiji-publications.github.io/](https://taiji-publications.github.io/)

### Local Development

1. Install Hugo (extended version):
   ```bash
   # macOS
   brew install hugo

   # Linux
   snap install hugo --channel=extended

   # Windows
   choco install hugo-extended
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/taiji-publications/TJ_info.git
   cd TJ_info
   ```

3. Install Python dependencies:
   ```bash
   make install
   # or
   pip install -r requirements.txt
   ```

4. Start the development server:
   ```bash
   make serve
   # or
   hugo server -D
   ```

5. Open your browser to `http://localhost:1313`

## Makefile Commands

All development tasks are available via `make`:

```bash
make help              # Show all available commands

# Environment
make install           # Install Python dependencies
make check-deps        # Check if dependencies are installed

# Database Operations
make validate          # Run all validation checks
make stats             # Show database statistics
make report            # Generate quality report

# Adding Papers
make add-doi DOI=xxx   # Add paper by DOI
make add-arxiv ID=xxx  # Add paper by arXiv ID
make add-interactive   # Interactive paper addition

# Citation Tracking
make find-citations ARXIV=xxx    # Find citations for paper
make find-citations-auto ARXIV=xxx  # Auto-add relevant citations
make update-citations            # Update all citation counts

# Export
make export            # Export to all formats (BibTeX, CSV, JSON, Markdown)
make export-bibtex     # Export to BibTeX
make export-csv        # Export to CSV

# Hugo Site
make serve             # Start dev server
make build             # Build static site
make sync              # Sync database to Hugo content

# Workflows
make deploy            # Full deploy: validate → sync → export → build

# Institutions
make import-institutions INPUT=file.xlsx  # Import institution data from Excel
```

## Contributing

We welcome contributions from the community! See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed instructions.

### Quick Contribution Guide

1. Fork this repository
2. Create a new branch for your contribution
3. Add your publication or talk using the provided templates
4. Submit a pull request

### Adding a Publication

**Option 1: Via Makefile (Recommended)**

```bash
# Add by DOI
make add-doi DOI=10.1103/PhysRevD.100.022003

# Add by arXiv ID
make add-arxiv ID=2401.12345

# Interactive mode
make add-interactive
```

**Option 2: Manual Entry**

Create a new file in `content/publications/` with the format `YYYY-MM-DD-short-title.md`:

```yaml
---
title: "Your Publication Title"
date: 2025-03-15
authors:
  - name: "Author Name"
    affiliation: "Institution"
journal: "Journal Name"
volume: "123"
pages: "456-789"
year: 2025
arxiv: "2503.12345"
doi: "10.1234/example"
keywords:
  - "gravitational waves"
  - "data analysis"
publication_type: "journal"
featured: false
---
```

### Adding a Talk

Create a new file in `content/talks/` with the format `YYYY-MM-DD-event-name.md`:

```yaml
---
title: "Your Talk Title"
date: 2025-06-20
speaker:
  name: "Speaker Name"
  affiliation: "Institution"
event: "Conference Name"
location: "City, Country"
talk_type: "conference"
slides_url: "https://example.com/slides.pdf"
video_url: "https://youtube.com/watch?v=..."
keywords:
  - "mission design"
---
```

## Project Structure

```
TJ_info/
├── .github/              # GitHub Actions workflows and templates
├── archetypes/           # Content templates
├── assets/               # CSS and JavaScript
├── config/               # Configuration files (taxonomy, schema)
├── content/              # Markdown content files
│   ├── publications/     # Publication entries
│   ├── talks/            # Talk entries
│   └── contribute/       # Contribution guidelines
├── data/                 # JSON database and cache
│   ├── papers.json       # Main publications database
│   ├── institutions.json # Taiji Alliance member institutions
│   └── api_cache/        # API response cache
├── database/             # Export files (BibTeX, CSV, etc.)
├── layouts/              # Hugo templates
├── reports/              # Generated quality reports
├── scripts/              # Python scripts
│   ├── lib/              # Core libraries (api_client, db_manager, etc.)
│   ├── add_paper.py      # Add papers by DOI/arXiv
│   ├── import_institutions.py  # Import institution data from Excel
│   ├── find_citations.py # Citation tracking
│   ├── sync_database.py  # Sync DB to Hugo
│   ├── export_data.py    # Multi-format export
│   └── validate_data.py  # Database validation
├── static/               # Static assets (images, downloads)
├── Makefile              # Development commands
├── requirements.txt      # Python dependencies
├── hugo.toml             # Hugo configuration
└── README.md             # This file
```

## Technology Stack

- **Static Site Generator**: Hugo (extended)
- **Styling**: Custom SCSS with LIGO-inspired design
- **Deployment**: GitHub Pages via GitHub Actions
- **Database**: JSON with Python management scripts
- **Citation Tracking**: Semantic Scholar, Crossref, arXiv, INSPIRE-HEP APIs
- **Validation**: Python scripts with JSON Schema

## Design

The site uses a LIGO-inspired academic design:
- Clean white background
- Navy blue (#000080) links and borders
- Light steel blue table headers
- Minimal, content-focused layout
- Mobile-first responsive design

## Citation Tracking

The portal includes a citation tracking system that:
- Fetches paper metadata from arXiv, Crossref, and Semantic Scholar
- Tracks citations using Semantic Scholar API
- Scores papers for Taiji relevance automatically
- Exports to BibTeX, CSV, JSON, and Markdown

### Updating Citation Counts

```bash
make update-citations
```

### Finding New Relevant Papers

```bash
# Find papers citing a Taiji publication
make find-citations ARXIV=2401.12345

# Auto-add papers with high relevance
make find-citations-auto ARXIV=2401.12345 MIN_REL=0.5
```

## Institution Data

The portal maintains a structured database of 65 Taiji Alliance member institutions (`data/institutions.json`), including bilingual names and cooperation types.

- **29 official partners** with cooperation categories
- **36 affiliate institutions**
- All entries have Chinese and English names

### Importing Institution Data

```bash
make import-institutions INPUT=/path/to/太极联盟信息整理.xlsx
```

The import script automatically handles data corrections (typo fixes, whitespace cleanup, missing English name completion).

## Maintenance

### Validation

```bash
make validate
```

### Export

```bash
# Export to all formats
make export

# Specific format
make export-bibtex
make export-csv
```

### Building

```bash
make build
```

The generated site will be in the `public/` directory.

## License

This project is open source. Content contributions should be properly attributed to their original authors.

## Contact

For questions or issues, please:
- Open an issue on GitHub
- Contact the maintainers

## Acknowledgments

This portal is maintained by the Taiji Collaboration and hosted by ICTP-AP (International Centre for Theoretical Physics Asia-Pacific).

---

**Taiji Mission**: China's space-based gravitational wave detection mission, designed to observe gravitational waves in the millihertz frequency band.
