# CLAUDE.md - Development Context & History

**Project**: Taiji Publications & Talks Portal
**Created**: 2025-04-09
**Last Updated**: 2025-04-09
**Status**: Initial Implementation Complete

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

**Technology Stack:**
- **Static Site Generator**: Hugo (extended version)
- **Styling**: Custom SCSS with Taiji/ICTP-AP branding (#8c0000 primary color)
- **Deployment**: GitHub Pages via GitHub Actions
- **Validation**: Python scripts for YAML schema checking
- **Data Format**: YAML frontmatter in Markdown files

### 中文版本

太极出版物与报告门户网站是一个使用Hugo构建的静态网站，用于展示与太极空间引力波探测项目相关的出版物和演讲。该网站设计为通过GitHub拉取请求进行社区维护，具有自动验证和部署功能。

**主要目标：**
- 提供太极相关出版物的集中、可搜索存储库
- 展示来自会议、研讨会和公共活动的演讲和报告
- 通过GitHub工作流程实现简便的社区贡献
- 通过自动验证保持高数据质量
- 以可访问、响应式的设计呈现内容

**技术栈：**
- **静态站点生成器**：Hugo（扩展版本）
- **样式**：自定义SCSS，采用太极/ICTP-AP品牌色（主色#8c0000）
- **部署**：通过GitHub Actions部署到GitHub Pages
- **验证**：用于YAML模式检查的Python脚本
- **数据格式**：Markdown文件中的YAML前置元数据

---

## Architecture Decisions

### Why Hugo?

1. **Performance**: Fast build times even with hundreds of publications
2. **Simplicity**: Single binary, no runtime dependencies
3. **Native Features**: Built-in taxonomies, data file support, RSS generation
4. **GitHub Pages**: Seamless deployment via GitHub Actions
5. **Community**: Large ecosystem and excellent documentation

### Why YAML Frontmatter?

1. **Human-Readable**: Easy for non-technical contributors to edit
2. **Git-Friendly**: Clear diffs for PR reviews
3. **Structured**: Enforces consistent data schema
4. **Hugo Native**: Direct support without additional processing
5. **Validation**: Easy to validate with Python scripts

### Design Philosophy

1. **Simplicity First**: Minimal dependencies, straightforward structure
2. **Community-Driven**: Easy contribution workflow via GitHub
3. **Data Quality**: Automated validation prevents errors
4. **Accessibility**: Responsive design, semantic HTML
5. **Maintainability**: Clear documentation, modular code

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
│   └── config/                     # Configuration data files
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
├── scripts/
│   ├── validate-publication.py     # Publication validator
│   └── validate-talk.py            # Talk validator
│
├── static/
│   ├── images/                     # Logo, favicon, etc.
│   └── downloads/                  # Static files
│
├── hugo.toml                       # Hugo configuration
├── README.md                       # Project documentation
├── CONTRIBUTING.md                 # Contribution guide
└── CLAUDE.md                       # This file
```

---

## Key Implementation Details

### Publications Page

**Features:**
- Sortable table with columns: Date, Title, Authors, Journal, Links
- Client-side filtering by year, type, and search term
- arXiv and DOI badges with direct links
- Responsive table design (horizontal scroll on mobile)

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

**Color Scheme (Taiji/ICTP-AP):**
- Primary: #8c0000 (dark red)
- Background: #ffffff (white)
- Text: #333333 (dark grey)
- Accent: #f5f5f5 (light grey)
- Hover: #a00000 (lighter red)

**Responsive Breakpoints:**
- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

### Validation

**Publication Validation:**
- Required fields: title, date, authors, year, keywords, publication_type
- Valid types: journal, conference, preprint
- Authors must be list of dicts with 'name' field
- Keywords must be list

**Talk Validation:**
- Required fields: title, date, speaker, event, talk_type, keywords
- Valid types: conference, seminar, workshop, colloquium, public
- Speaker must be dict with 'name' field
- Keywords must be list

---

## Common Tasks

### Add a New Publication

```bash
# Create new file
hugo new content/publications/YYYY-MM-DD-short-title.md

# Edit the file with publication details
# Validate
python scripts/validate-publication.py

# Commit and push
git add content/publications/YYYY-MM-DD-short-title.md
git commit -m "Add publication: Title"
git push
```

### Add a New Talk

```bash
# Create new file
hugo new content/talks/YYYY-MM-DD-event-name.md

# Edit the file with talk details
# Validate
python scripts/validate-talk.py

# Commit and push
git add content/talks/YYYY-MM-DD-event-name.md
git commit -m "Add talk: Event Name"
git push
```

### Local Development

```bash
# Start development server
hugo server -D

# Build for production
hugo --gc --minify

# Run validation
python scripts/validate-publication.py
python scripts/validate-talk.py
```

### Update Styling

```bash
# Edit SCSS files in assets/css/
# Hugo will automatically recompile on save

# Main stylesheet: assets/css/main.scss
# Variables: assets/css/_variables.scss
```

---

## Modification History

### 2025-04-09: Initial Implementation

**Created:**
- Hugo site structure with custom theme
- Publications and talks content types
- Responsive layouts with Taiji branding
- JavaScript filtering and sorting
- GitHub Actions workflows for deployment and validation
- Python validation scripts
- Comprehensive documentation (README, CONTRIBUTING, CLAUDE.md)
- Example publications (5 entries)
- Example talks (5 entries across all types)
- Issue and PR templates

**Key Files:**
- `hugo.toml`: Site configuration
- `layouts/index.html`: Homepage
- `layouts/publications/list.html`: Publications table
- `layouts/talks/list.html`: Talks grouped view
- `assets/css/main.scss`: Main stylesheet
- `assets/js/table-filter.js`: Filtering logic
- `.github/workflows/hugo-build.yml`: Deployment workflow
- `scripts/validate-publication.py`: Publication validator
- `scripts/validate-talk.py`: Talk validator

**Design Decisions:**
- Used Hugo's native taxonomies for keywords and talk types
- Implemented client-side filtering for better UX
- Chose YAML frontmatter for human-readable data format
- Adopted LIGO-style publication table design
- Implemented mobile-first responsive design

---

## Future Enhancements

### Short-term (Next 3 months)

1. **Search Functionality**
   - Full-text search across publications and talks
   - Search by author, keyword, or content
   - Implement with Lunr.js or similar

2. **BibTeX Export**
   - Generate BibTeX entries from publication data
   - Bulk export functionality
   - Individual publication BibTeX download

3. **Statistics Dashboard**
   - Publications per year chart
   - Talk distribution by type
   - Keyword cloud visualization
   - Author collaboration network

4. **Enhanced Filtering**
   - Multi-select keyword filtering
   - Author search and filtering
   - Date range selection
   - Advanced query builder

### Medium-term (3-6 months)

1. **RSS Feeds**
   - Per-category RSS feeds
   - New publications feed
   - Upcoming talks feed

2. **ORCID Integration**
   - Link authors to ORCID profiles
   - Import publication data from ORCID
   - Author profile pages

3. **Automated arXiv Scraping**
   - Monitor arXiv for Taiji-related papers
   - Automated PR creation for new papers
   - Email notifications for maintainers

4. **Multi-language Support**
   - Chinese translation of interface
   - Bilingual content support
   - Language switcher

### Long-term (6+ months)

1. **API Endpoint**
   - JSON API for programmatic access
   - GraphQL interface
   - Rate limiting and authentication

2. **Advanced Analytics**
   - Citation tracking
   - Impact metrics
   - Collaboration network analysis

3. **Interactive Visualizations**
   - Timeline of publications
   - Geographic distribution of talks
   - Topic evolution over time

4. **Integration with Other Databases**
   - ADS (Astrophysics Data System)
   - INSPIRE-HEP
   - Google Scholar

---

## Troubleshooting

### Common Issues

**Hugo build fails:**
- Check Hugo version (requires extended version)
- Verify YAML frontmatter syntax
- Ensure all required fields are present

**Validation errors:**
- Run validation scripts locally
- Check field types (list vs string vs dict)
- Verify publication_type and talk_type values

**Styling not updating:**
- Clear browser cache
- Check SCSS syntax
- Restart Hugo server

**GitHub Actions failing:**
- Check workflow logs
- Verify Python dependencies
- Ensure file paths are correct

### Debug Commands

```bash
# Check Hugo version
hugo version

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('file.md').read().split('---')[1])"

# Test build
hugo --gc --minify --verbose

# Check for broken links
hugo --gc --minify && htmlproofer public/
```

---

## Development Guidelines

### Code Style

**SCSS:**
- Use variables for colors and spacing
- Follow BEM naming convention
- Mobile-first media queries
- Comment complex selectors

**JavaScript:**
- Use vanilla JS (no frameworks)
- Add comments for complex logic
- Handle edge cases gracefully
- Test across browsers

**HTML:**
- Semantic HTML5 elements
- Accessible markup (ARIA labels)
- Proper heading hierarchy
- Valid HTML

**YAML:**
- Consistent indentation (2 spaces)
- Use quotes for strings with special characters
- Pipe syntax for multi-line text
- Alphabetical field order (optional)

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

**Pull Requests:**
- Fill out PR template completely
- Ensure CI passes
- Request review from maintainers
- Respond to feedback promptly

---

## Contact & Support

**Maintainers:**
- GitHub: [@taiji-publications](https://github.com/taiji-publications)
- Email: [To be added]

**Resources:**
- Hugo Documentation: https://gohugo.io/documentation/
- GitHub Pages: https://pages.github.com/
- Taiji Mission: https://ictp-ap.org/

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

---

**Last Updated**: 2025-04-09
**Version**: 1.0.0
**Status**: Production Ready
