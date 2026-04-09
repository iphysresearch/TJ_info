# Contributing to Taiji Publications & Talks Portal

Thank you for your interest in contributing to the Taiji Publications & Talks portal! This guide will help you submit publications and talks to our collection.

## Table of Contents

- [Getting Started](#getting-started)
- [Contribution Workflow](#contribution-workflow)
- [Adding Publications](#adding-publications)
- [Adding Talks](#adding-talks)
- [Style Guidelines](#style-guidelines)
- [Validation](#validation)
- [Questions and Support](#questions-and-support)

## Getting Started

### Prerequisites

- A GitHub account
- Basic familiarity with Markdown and YAML
- Git installed on your computer (optional, but recommended)

### Fork the Repository

1. Navigate to the [TJ_info repository](https://github.com/taiji-publications/TJ_info)
2. Click the "Fork" button in the top-right corner
3. Clone your fork to your local machine:
   ```bash
   git clone https://github.com/YOUR-USERNAME/TJ_info.git
   cd TJ_info
   ```

## Contribution Workflow

1. **Create a new branch** for your contribution:
   ```bash
   git checkout -b add-publication-name
   ```

2. **Add your content** following the templates below

3. **Validate your changes** (optional but recommended):
   ```bash
   python scripts/validate-publication.py
   python scripts/validate-talk.py
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add publication: Title of Paper"
   ```

5. **Push to your fork**:
   ```bash
   git push origin add-publication-name
   ```

6. **Create a Pull Request** on GitHub

## Adding Publications

### File Naming Convention

Create a new file in `content/publications/` with the format:
```
YYYY-MM-DD-short-descriptive-title.md
```

Example: `2025-03-15-taiji-calibration-analysis.md`

### Publication Template

```yaml
---
title: "Full Title of the Publication"
date: 2025-03-15
authors:
  - name: "First Author"
    affiliation: "Institution Name"
  - name: "Second Author"
    affiliation: "Another Institution"
journal: "Journal Name"
volume: "123"
pages: "456-789"
year: 2025
arxiv: "2503.12345"
doi: "10.1103/PhysRevD.123.456789"
keywords:
  - "gravitational waves"
  - "space-based detection"
  - "data analysis"
abstract: |
  Brief abstract of the publication. This should be a concise summary
  of the main findings and contributions of the work.
publication_type: "journal"  # Options: journal, conference, preprint
featured: false
---

Optional extended description or notes about the publication can go here
in Markdown format.
```

### Required Fields

- `title`: Full publication title
- `date`: Publication date (YYYY-MM-DD)
- `authors`: List of authors with names and affiliations
- `year`: Publication year
- `keywords`: List of relevant keywords
- `publication_type`: One of: journal, conference, preprint

### Optional Fields

- `journal`: Journal name (for journal articles)
- `volume`: Volume number
- `pages`: Page range
- `arxiv`: arXiv identifier (e.g., "2503.12345")
- `doi`: Digital Object Identifier
- `abstract`: Publication abstract
- `featured`: Set to `true` for highlighted publications

### Keywords

Use keywords from the following categories:
- **Mission**: mission design, instrumentation, calibration, pathfinder
- **Data Analysis**: parameter estimation, time-delay interferometry, Bayesian methods, machine learning
- **Sources**: black hole binaries, EMRIs, verification binaries, stochastic background
- **Physics**: general relativity tests, Lorentz violation, primordial black holes
- **Cosmology**: dark-siren cosmology, Hubble constant, multi-band observations

## Adding Talks

### File Naming Convention

Create a new file in `content/talks/` with the format:
```
YYYY-MM-DD-event-or-venue-name.md
```

Example: `2025-04-15-aps-april-meeting.md`

### Talk Template

```yaml
---
title: "Title of the Talk"
date: 2025-04-15
speaker:
  name: "Speaker Name"
  affiliation: "Institution"
event: "Conference or Event Name"
location: "City, Country"
talk_type: "conference"  # Options: conference, seminar, workshop, colloquium, public
slides_url: "https://example.com/slides.pdf"
video_url: "https://youtube.com/watch?v=..."
abstract: |
  Brief description of the talk content and main topics covered.
keywords:
  - "mission design"
  - "science objectives"
---

Optional additional notes or summary of the talk can go here.
```

### Required Fields

- `title`: Talk title
- `date`: Date of the talk (YYYY-MM-DD)
- `speaker`: Speaker information (name and affiliation)
- `event`: Event or venue name
- `talk_type`: One of: conference, seminar, workshop, colloquium, public
- `keywords`: List of relevant keywords

### Optional Fields

- `location`: City and country
- `slides_url`: Link to presentation slides
- `video_url`: Link to video recording
- `abstract`: Talk abstract or description

### Talk Types

- **conference**: Presentations at academic conferences
- **seminar**: Department or institute seminars
- **workshop**: Technical workshops and collaboration meetings
- **colloquium**: Departmental colloquia
- **public**: Public lectures and outreach events

## Style Guidelines

### Formatting

- Use proper capitalization for titles (title case)
- Include full author names (not just initials)
- Provide complete institutional affiliations
- Use standard journal abbreviations
- Format DOIs without the "https://doi.org/" prefix

### Content Quality

- Ensure all information is accurate and complete
- Verify that links are working and accessible
- Use clear, concise language in abstracts
- Choose appropriate and specific keywords
- Proofread for spelling and grammar

### Markdown

- Use standard Markdown formatting
- Keep content concise and well-organized
- Use proper heading levels (##, ###)
- Include line breaks for readability

## Validation

Before submitting your pull request, validate your content:

```bash
# Validate publications
python scripts/validate-publication.py

# Validate talks
python scripts/validate-talk.py
```

The validation scripts check:
- Required fields are present
- YAML syntax is correct
- Field types are appropriate
- Values are within allowed options

## Pull Request Guidelines

When submitting a pull request:

1. **Use a descriptive title**: "Add publication: [Title]" or "Add talk: [Event]"
2. **Fill out the PR template** completely
3. **Check all boxes** in the checklist
4. **Provide context** if needed in the description
5. **Be responsive** to reviewer feedback

### Review Process

1. Automated validation runs on your PR
2. Maintainers review the content for accuracy and completeness
3. Feedback may be provided for revisions
4. Once approved, your contribution is merged
5. The site automatically rebuilds and deploys

## Questions and Support

### Getting Help

- **Documentation**: Check this guide and the README
- **Issues**: Search existing issues or open a new one
- **Discussions**: Use GitHub Discussions for questions

### Reporting Issues

If you find errors in existing content:

1. Open an issue describing the problem
2. Include the file path and specific error
3. Suggest a correction if possible

### Contact

For direct assistance, contact the maintainers:
- GitHub: [@taiji-publications](https://github.com/taiji-publications)
- Email: [contact information]

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please:

- Be respectful and professional
- Provide constructive feedback
- Focus on the content, not the contributor
- Follow academic integrity standards
- Properly attribute all work

## Recognition

Contributors will be acknowledged in:
- Git commit history
- GitHub contributors list
- Annual acknowledgments (for significant contributions)

Thank you for helping build this valuable resource for the Taiji community!

---

**Questions?** Open an issue or reach out to the maintainers.
