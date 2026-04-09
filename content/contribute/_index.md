---
title: "Contribute"
---

## How to Contribute

We welcome contributions from the community to help maintain this comprehensive resource of Taiji-related publications and talks.

### Adding a Publication

1. Fork the [GitHub repository](https://github.com/taiji-publications/TJ_info)
2. Create a new file in `content/publications/` with the naming format: `YYYY-MM-DD-short-title.md`
3. Use the publication template (see below)
4. Fill in all required fields
5. Submit a pull request

### Publication Template

```yaml
---
title: "Full publication title"
date: 2024-03-15
authors:
  - name: "Author One"
    affiliation: "Institution A"
  - name: "Author Two"
    affiliation: "Institution B"
journal: "Physical Review D"
volume: "109"
pages: "064001"
year: 2024
arxiv: "2401.12345"
doi: "10.1103/PhysRevD.109.064001"
keywords:
  - "gravitational waves"
  - "space-based detection"
  - "mission design"
abstract: |
  Brief abstract text here...
publication_type: "journal"  # journal, conference, preprint
featured: false
---

Optional extended description in Markdown.
```

### Adding a Talk

1. Fork the repository
2. Create a new file in `content/talks/` with the naming format: `YYYY-MM-DD-event-name.md`
3. Use the talk template (see below)
4. Fill in all required fields
5. Submit a pull request

### Talk Template

```yaml
---
title: "Talk title"
date: 2024-06-20
speaker:
  name: "Speaker Name"
  affiliation: "Institution"
event: "Conference/Seminar Name"
location: "City, Country"
talk_type: "conference"  # conference, seminar, workshop, colloquium, public
slides_url: "https://example.com/slides.pdf"
video_url: "https://youtube.com/watch?v=..."
abstract: |
  Talk abstract...
keywords:
  - "data analysis"
  - "mission design"
---

Additional notes or summary.
```

### Guidelines

- Ensure all information is accurate and complete
- Use consistent formatting for author names and affiliations
- Include DOI and arXiv links when available
- Choose appropriate keywords from the controlled vocabulary
- For talks, provide links to slides or video recordings when possible

### Questions?

If you have questions about contributing, please open an issue on GitHub or contact the maintainers.
