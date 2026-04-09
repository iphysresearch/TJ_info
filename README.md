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
- **BibTeX export** functionality
- **Multi-band search** across titles, authors, and keywords

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

3. Start the development server:
   ```bash
   hugo server -D
   ```

4. Open your browser to `http://localhost:1313`

## Contributing

We welcome contributions from the community! See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed instructions.

### Quick Contribution Guide

1. Fork this repository
2. Create a new branch for your contribution
3. Add your publication or talk using the provided templates
4. Submit a pull request

### Adding a Publication

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
├── content/              # Markdown content files
│   ├── publications/     # Publication entries
│   ├── talks/            # Talk entries
│   └── contribute/       # Contribution guidelines
├── data/                 # Data files
├── layouts/              # Hugo templates
├── scripts/              # Validation scripts
├── static/               # Static assets (images, downloads)
├── hugo.toml             # Hugo configuration
└── README.md             # This file
```

## Technology Stack

- **Static Site Generator**: Hugo (extended)
- **Styling**: Custom SCSS with Taiji branding
- **Deployment**: GitHub Pages via GitHub Actions
- **Validation**: Python scripts for YAML schema validation

## Design

The site uses the Taiji/ICTP-AP color scheme:
- Primary color: Dark red (#8c0000)
- Clean, responsive layout
- LIGO-inspired publication tables
- Mobile-first design approach

## Maintenance

### Validation

Run validation scripts locally before submitting:

```bash
python scripts/validate-publication.py
python scripts/validate-talk.py
```

### Building

Build the site locally:

```bash
hugo --gc --minify
```

The generated site will be in the `public/` directory.

## License

This project is open source. Content contributions should be properly attributed to their original authors.

## Contact

For questions or issues, please:
- Open an issue on GitHub
- Contact the maintainers at [contact information]

## Acknowledgments

This portal is maintained by the Taiji Collaboration and hosted by ICTP-AP (International Centre for Theoretical Physics Asia-Pacific).

---

**Taiji Mission**: China's space-based gravitational wave detection mission, designed to observe gravitational waves in the millihertz frequency band.
