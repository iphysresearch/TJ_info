# ═══════════════════════════════════════════════════════════════════════════════
# TJ_info Makefile - Taiji Publications Portal Development Commands
# 太极出版物门户开发命令
# ═══════════════════════════════════════════════════════════════════════════════

.PHONY: help install validate add-paper find-citations sync export serve deploy \
        validate-format validate-dupes validate-citations add-doi add-arxiv \
        add-interactive find-citations-auto find-citations-dry update-citations \
        find-citations-doi find-citations-doi-auto find-citations-doi-dry \
        export-bibtex export-csv build full-update report stats check-deps clean \
        fix-dates fix-authors import-institutions

# Default Python interpreter
PYTHON ?= python3

# Default values for optional parameters
LIMIT ?= 10
MIN_REL ?= 0.5

# ═══════════════════════════════════════════════════════════════════════════════
# HELP - 帮助信息
# ═══════════════════════════════════════════════════════════════════════════════
help:
	@echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
	@echo "║          Taiji Publications Portal - Development Commands                     ║"
	@echo "║                   太极出版物门户 - 开发命令                                   ║"
	@echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📦 Environment / 环境"
	@echo "   make install          - Install Python dependencies / 安装Python依赖"
	@echo "   make check-deps       - Check if dependencies are installed / 检查依赖"
	@echo "   make clean            - Clean cache and build files / 清理缓存和构建文件"
	@echo ""
	@echo "✅ Validation / 验证"
	@echo "   make validate         - Run all validation checks / 运行所有验证检查"
	@echo "   make validate-format  - Check data format / 检查数据格式"
	@echo "   make validate-dupes   - Check for duplicates / 检查重复项"
	@echo "   make validate-citations - Validate citation data / 验证引用数据"
	@echo ""
	@echo "📄 Add Papers / 添加论文"
	@echo "   make add-doi DOI=xxx  - Add paper by DOI / 通过DOI添加论文"
	@echo "   make add-arxiv ID=xxx - Add paper by arXiv ID / 通过arXiv ID添加论文"
	@echo "   make add-interactive  - Interactive paper addition / 交互式添加论文"
	@echo ""
	@echo "🔗 Citation Tracking / 引用追踪"
	@echo "   make find-citations ARXIV=xxx           - Find citations (arXiv)"
	@echo "   make find-citations-auto ARXIV=xxx      - Auto-add citations (arXiv)"
	@echo "   make find-citations-dry ARXIV=xxx       - Dry run (arXiv)"
	@echo "   make find-citations-doi DOI=xxx         - Find citations (DOI)"
	@echo "   make find-citations-doi-auto DOI=xxx    - Auto-add citations (DOI)"
	@echo "   make find-citations-doi-dry DOI=xxx     - Dry run (DOI)"
	@echo "   make update-citations                   - Update all citation counts"
	@echo ""
	@echo "📤 Export / 导出"
	@echo "   make export           - Export to all formats / 导出所有格式"
	@echo "   make export-bibtex    - Export to BibTeX / 导出BibTeX"
	@echo "   make export-csv       - Export to CSV / 导出CSV"
	@echo ""
	@echo "🔄 Sync & Build / 同步和构建"
	@echo "   make sync             - Sync database to Hugo content / 同步数据库到Hugo"
	@echo "   make serve            - Start Hugo dev server / 启动Hugo开发服务器"
	@echo "   make build            - Build static site / 构建静态站点"
	@echo ""
	@echo "🔧 Data Fixes / 数据修复"
	@echo "   make fix-dates        - Fix paper dates via Crossref / 修复论文日期"
	@echo "   make fix-authors      - Expand abbreviated author names / 展开缩写作者名"
	@echo ""
	@echo "🏛️  Institutions / 成员单位"
	@echo "   make import-institutions INPUT=file.xlsx - Import institution data / 导入成员单位数据"
	@echo ""
	@echo "🚀 Workflows / 工作流"
	@echo "   make deploy           - Full deploy: validate → sync → export → build"
	@echo "   make full-update      - Update: validate → export → sync"
	@echo ""
	@echo "📊 Reports / 报告"
	@echo "   make report           - Generate quality report / 生成质量报告"
	@echo "   make stats            - Show database statistics / 显示数据库统计"
	@echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# ENVIRONMENT / 环境
# ═══════════════════════════════════════════════════════════════════════════════
install:
	@echo "📦 Installing Python dependencies..."
	pip install -r requirements.txt
	@echo "✅ Dependencies installed!"

check-deps:
	@echo "🔍 Checking dependencies..."
	@$(PYTHON) -c "import yaml" && echo "  ✓ PyYAML" || echo "  ✗ PyYAML (run: pip install PyYAML)"
	@$(PYTHON) -c "import requests" && echo "  ✓ requests" || echo "  ✗ requests (run: pip install requests)"
	@$(PYTHON) -c "import bibtexparser" && echo "  ✓ bibtexparser" || echo "  ✗ bibtexparser (run: pip install bibtexparser)"
	@$(PYTHON) -c "import jsonschema" && echo "  ✓ jsonschema" || echo "  ✗ jsonschema (run: pip install jsonschema)"
	@$(PYTHON) -c "import dateutil" && echo "  ✓ python-dateutil" || echo "  ✗ python-dateutil (run: pip install python-dateutil)"
	@$(PYTHON) -c "import tqdm" && echo "  ✓ tqdm" || echo "  ✗ tqdm (run: pip install tqdm)"
	@which hugo > /dev/null && echo "  ✓ Hugo" || echo "  ✗ Hugo (install from: https://gohugo.io)"
	@echo ""

clean:
	@echo "🧹 Cleaning cache and build files..."
	rm -rf data/api_cache/arxiv/*
	rm -rf data/api_cache/crossref/*
	rm -rf data/api_cache/semantic_scholar/*
	rm -rf public/
	rm -rf resources/_gen/
	@echo "✅ Clean complete!"

# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION / 验证
# ═══════════════════════════════════════════════════════════════════════════════
validate:
	@echo "✅ Running all validation checks..."
	$(PYTHON) scripts/validate_data.py

validate-format:
	@echo "📋 Checking data format..."
	$(PYTHON) scripts/validate_data.py --check format

validate-dupes:
	@echo "🔍 Checking for duplicates..."
	$(PYTHON) scripts/validate_data.py --check duplicates

validate-citations:
	@echo "🔗 Validating citation data..."
	$(PYTHON) scripts/validate_data.py --check citations

# ═══════════════════════════════════════════════════════════════════════════════
# ADD PAPERS / 添加论文
# ═══════════════════════════════════════════════════════════════════════════════
add-doi:
ifndef DOI
	$(error DOI is required. Usage: make add-doi DOI=10.1103/PhysRevD.100.022003)
endif
	@echo "📄 Adding paper by DOI: $(DOI)"
	$(PYTHON) scripts/add_paper.py --doi "$(DOI)"

add-arxiv:
ifndef ID
	$(error ID is required. Usage: make add-arxiv ID=2401.12345)
endif
	@echo "📄 Adding paper by arXiv ID: $(ID)"
	$(PYTHON) scripts/add_paper.py --arxiv "$(ID)"

add-interactive:
	@echo "📄 Starting interactive paper addition..."
	$(PYTHON) scripts/add_paper.py --interactive

# ═══════════════════════════════════════════════════════════════════════════════
# CITATION TRACKING / 引用追踪
# ═══════════════════════════════════════════════════════════════════════════════
find-citations:
ifndef ARXIV
	$(error ARXIV is required. Usage: make find-citations ARXIV=2401.12345)
endif
	@echo "🔗 Finding citations for arXiv:$(ARXIV)..."
	$(PYTHON) scripts/find_citations.py --arxiv "$(ARXIV)"

find-citations-auto:
ifndef ARXIV
	$(error ARXIV is required. Usage: make find-citations-auto ARXIV=2401.12345)
endif
	@echo "🔗 Auto-adding citations for arXiv:$(ARXIV)..."
	$(PYTHON) scripts/find_citations.py --arxiv "$(ARXIV)" --auto --limit $(LIMIT) --min-relevance $(MIN_REL)

find-citations-dry:
ifndef ARXIV
	$(error ARXIV is required. Usage: make find-citations-dry ARXIV=2401.12345)
endif
	@echo "🔗 Dry run: finding citations for arXiv:$(ARXIV)..."
	$(PYTHON) scripts/find_citations.py --arxiv "$(ARXIV)" --dry-run

# DOI-based citation tracking
find-citations-doi:
ifndef DOI
	$(error DOI is required. Usage: make find-citations-doi DOI=10.1103/PhysRevD.111.084023)
endif
	@echo "🔗 Finding citations for DOI:$(DOI)..."
	$(PYTHON) scripts/find_citations.py --doi "$(DOI)" --limit $(LIMIT) --min-relevance $(MIN_REL)

find-citations-doi-auto:
ifndef DOI
	$(error DOI is required. Usage: make find-citations-doi-auto DOI=xxx)
endif
	@echo "🔗 Auto-adding citations for DOI:$(DOI)..."
	$(PYTHON) scripts/find_citations.py --doi "$(DOI)" --limit $(LIMIT) --min-relevance $(MIN_REL) --auto

find-citations-doi-dry:
ifndef DOI
	$(error DOI is required. Usage: make find-citations-doi-dry DOI=xxx)
endif
	@echo "🔗 Dry run for DOI:$(DOI)..."
	$(PYTHON) scripts/find_citations.py --doi "$(DOI)" --limit $(LIMIT) --min-relevance $(MIN_REL) --dry-run

update-citations:
	@echo "🔄 Updating citation counts for all papers..."
	$(PYTHON) scripts/update_citations.py

# ═══════════════════════════════════════════════════════════════════════════════
# EXPORT / 导出
# ═══════════════════════════════════════════════════════════════════════════════
export:
	@echo "📤 Exporting to all formats..."
	$(PYTHON) scripts/export_data.py --all

export-bibtex:
	@echo "📤 Exporting to BibTeX..."
	$(PYTHON) scripts/export_data.py --format bibtex --output database/papers.bib

export-csv:
	@echo "📤 Exporting to CSV..."
	$(PYTHON) scripts/export_data.py --format csv --output database/papers.csv

# ═══════════════════════════════════════════════════════════════════════════════
# DATA FIXES / 数据修复
# ═══════════════════════════════════════════════════════════════════════════════
fix-dates:
	@echo "📅 Fixing paper dates..."
	$(PYTHON) scripts/fix_dates.py

fix-authors:
	@echo "👤 Fixing abbreviated author names..."
	$(PYTHON) scripts/fix_authors.py

# ═══════════════════════════════════════════════════════════════════════════════
# INSTITUTIONS / 成员单位管理
# ═══════════════════════════════════════════════════════════════════════════════
import-institutions:
ifndef INPUT
	$(error INPUT is required. Usage: make import-institutions INPUT=/path/to/太极联盟信息整理.xlsx)
endif
	@echo "🏛️  Importing institution data..."
	$(PYTHON) scripts/import_institutions.py --input "$(INPUT)" --output data/institutions.json

# ═══════════════════════════════════════════════════════════════════════════════
# SYNC & BUILD / 同步和构建
# ═══════════════════════════════════════════════════════════════════════════════
sync:
	@echo "🔄 Syncing database to Hugo content..."
	$(PYTHON) scripts/sync_database.py

serve:
	@echo "🌐 Starting Hugo development server..."
	hugo server -D

build:
	@echo "🏗️ Building static site..."
	hugo --gc --minify

# ═══════════════════════════════════════════════════════════════════════════════
# WORKFLOWS / 工作流
# ═══════════════════════════════════════════════════════════════════════════════
deploy: validate sync export build
	@echo ""
	@echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
	@echo "║                         🚀 Deploy Complete! 部署完成!                         ║"
	@echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
	@echo ""

full-update: validate export sync
	@echo ""
	@echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
	@echo "║                        ✅ Update Complete! 更新完成!                          ║"
	@echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
	@echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# REPORTS / 报告
# ═══════════════════════════════════════════════════════════════════════════════
report:
	@echo "📊 Generating quality report..."
	$(PYTHON) scripts/generate_report.py

stats:
	@echo "📊 Database statistics..."
	$(PYTHON) scripts/validate_data.py --stats
