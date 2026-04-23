#!/usr/bin/env python3
"""
Sync Database to Hugo Content
同步数据库到 Hugo 内容

This script synchronizes the papers.json database to Hugo markdown files
and data files.

Usage:
    python scripts/sync_database.py
    python scripts/sync_database.py --dry-run
"""

import sys
import json
import re
import argparse
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.db_manager import load_database, get_all_entries

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
DATABASE_PATH = Path("data/papers.json")
HUGO_CONTENT_PATH = Path("content/publications")
HUGO_DATA_PATH = Path("data")


# DOI prefix → journal abbreviation mapping (ISO 4 standard, longest prefix match first)
DOI_PREFIX_ABBREV = {
    # Physical Review family
    "10.1103/PhysRevD": "Phys. Rev. D",
    "10.1103/PhysRevLett": "Phys. Rev. Lett.",
    "10.1103/PhysRevX": "Phys. Rev. X",
    "10.1103/PhysRevAccelBeams": "Phys. Rev. Accel. Beams",
    "10.1103/PhysRevApplied": "Phys. Rev. Appl.",
    "10.1103/RevModPhys": "Rev. Mod. Phys.",
    "10.1103/PhysRevResearch": "Phys. Rev. Res.",
    "10.1103/Physics": "Physics",
    "10.1103/": "Phys. Rev.",
    # IOP journals
    "10.1088/1475-7516": "J. Cosmol. Astropart. Phys.",
    "10.1088/1361-6382": "Class. Quantum Grav.",
    "10.1088/0264-9381": "Class. Quantum Grav.",
    "10.1088/1674-1137": "Chin. Phys. C",
    "10.1088/1742-6596": "J. Phys. Conf. Ser.",
    "10.1088/1674-4527": "Res. Astron. Astrophys.",
    "10.1088/1361-6633": "Rep. Prog. Phys.",
    "10.1088/0256-307X": "Chin. Phys. Lett.",
    "10.1088/1367-2630": "New J. Phys.",
    "10.1088/": "IOP",
    # AAS / Astrophysics journals
    "10.3847/1538-4357": "Astrophys. J.",
    "10.3847/2041-8213": "Astrophys. J. Lett.",
    "10.3847/1538-4365": "Astrophys. J. Suppl. Ser.",
    "10.3847/0004-637X": "Astrophys. J.",
    "10.3847/2515-5172": "Res. Notes AAS",
    "10.3847/": "AAS",
    "10.1086/": "Astron. J.",
    # Springer / EPJ / JHEP
    "10.1007/JHEP": "J. High Energy Phys.",
    "10.1007/s41114": "Living Rev. Relativ.",
    "10.1007/s10714": "Gen. Relativ. Gravit.",
    "10.1007/s11433": "Sci. China Phys. Mech. Astron.",
    "10.1007/s10909": "J. Low Temp. Phys.",
    "10.1007/s12210": "Rend. Lincei",
    "10.1007/s10686": "Exp. Astron.",
    "10.1007/s12567": "CEAS Space J.",
    "10.1007/": "Springer",
    "10.1140/epjc": "Eur. Phys. J. C",
    "10.1140/epjp": "Eur. Phys. J. Plus",
    "10.1140/epjst": "Eur. Phys. J. Spec. Top.",
    "10.1140/": "Eur. Phys. J.",
    # Elsevier
    "10.1016/j.physletb": "Phys. Lett. B",
    "10.1016/j.nuclphysb": "Nucl. Phys. B",
    "10.1016/j.dark": "Phys. Dark Universe",
    "10.1016/j.physrep": "Phys. Rep.",
    "10.1016/j.astropartphys": "Astropart. Phys.",
    "10.1016/j.asr": "Adv. Space Res.",
    "10.1016/j.cjph": "Chin. J. Phys.",
    "10.1016/j.scib": "Sci. Bull.",
    "10.1016/j.rinp": "Results Phys.",
    "10.1016/": "Elsevier",
    # A&A
    "10.1051/0004-6361": "Astron. Astrophys.",
    "10.1051/": "EDP Sci.",
    # MNRAS
    "10.1093/mnras": "Mon. Not. R. Astron. Soc.",
    "10.1093/nsr": "Natl. Sci. Rev.",
    "10.1093/ptep": "Prog. Theor. Exp. Phys.",
    "10.1093/": "OUP",
    # MDPI
    "10.3390/sym": "Symmetry",
    "10.3390/universe": "Universe",
    "10.3390/sensors": "Sensors",
    "10.3390/galaxies": "Galaxies",
    "10.3390/": "MDPI",
    # World Scientific
    "10.1142/S0217751X": "Int. J. Mod. Phys. A",
    "10.1142/S0218271X": "Int. J. Mod. Phys. D",
    "10.1142/S0217732": "Mod. Phys. Lett. A",
    "10.1142/": "World Sci.",
    # Nature
    "10.1038/s41586": "Nature",
    "10.1038/s41550": "Nat. Astron.",
    "10.1038/s41567": "Nat. Phys.",
    "10.1038/": "Nature",
    # Science
    "10.1126/science": "Science",
    "10.1126/sciadv": "Sci. Adv.",
    "10.1126/": "Science",
    # Optics
    "10.1364/AO": "Appl. Opt.",
    "10.1364/OE": "Opt. Express",
    "10.1364/OL": "Opt. Lett.",
    "10.1364/": "Optica",
    # Chinese journals
    "10.1360/": "Sci. Sin.",
    "10.11728/cjss": "Chin. J. Space Sci.",
    # IEEE
    "10.1109/": "IEEE",
    # AIP
    "10.1063/": "AIP",
    # Wiley
    "10.1002/": "Wiley",
    # AAAS
    "10.1146/annurev": "Annu. Rev. Astron. Astrophys.",
    # Living Reviews
    "10.1007/lrr": "Living Rev. Relativ.",
    # Other
    "10.3389/": "Front.",
    "10.1134/": "JETP",
    "10.1017/": "Cambridge Univ. Press",
}

# Full journal name → ISO 4 abbreviation fallback
JOURNAL_NAME_ABBREV = {
    "Physical Review D": "Phys. Rev. D",
    "Physical Review Letters": "Phys. Rev. Lett.",
    "Physical Review X": "Phys. Rev. X",
    "Reviews of Modern Physics": "Rev. Mod. Phys.",
    "Physical Review Research": "Phys. Rev. Res.",
    "Journal of Cosmology and Astroparticle Physics": "J. Cosmol. Astropart. Phys.",
    "Classical and Quantum Gravity": "Class. Quantum Grav.",
    "Chinese Physics C": "Chin. Phys. C",
    "Research in Astronomy and Astrophysics": "Res. Astron. Astrophys.",
    "The Astrophysical Journal": "Astrophys. J.",
    "Astrophysical Journal": "Astrophys. J.",
    "The Astrophysical Journal Letters": "Astrophys. J. Lett.",
    "Astrophysical Journal Letters": "Astrophys. J. Lett.",
    "The Astrophysical Journal Supplement Series": "Astrophys. J. Suppl. Ser.",
    "Journal of High Energy Physics": "J. High Energy Phys.",
    "Living Reviews in Relativity": "Living Rev. Relativ.",
    "General Relativity and Gravitation": "Gen. Relativ. Gravit.",
    "Science China Physics, Mechanics & Astronomy": "Sci. China Phys. Mech. Astron.",
    "Science China Physics Mechanics and Astronomy": "Sci. China Phys. Mech. Astron.",
    "European Physical Journal C": "Eur. Phys. J. C",
    "The European Physical Journal C": "Eur. Phys. J. C",
    "European Physical Journal Plus": "Eur. Phys. J. Plus",
    "Physics Letters B": "Phys. Lett. B",
    "Nuclear Physics B": "Nucl. Phys. B",
    "Physics of the Dark Universe": "Phys. Dark Universe",
    "Physics Reports": "Phys. Rep.",
    "Astroparticle Physics": "Astropart. Phys.",
    "Advances in Space Research": "Adv. Space Res.",
    "Science Bulletin": "Sci. Bull.",
    "Astronomy & Astrophysics": "Astron. Astrophys.",
    "Astronomy and Astrophysics": "Astron. Astrophys.",
    "Monthly Notices of the Royal Astronomical Society": "Mon. Not. R. Astron. Soc.",
    "National Science Review": "Natl. Sci. Rev.",
    "Progress of Theoretical and Experimental Physics": "Prog. Theor. Exp. Phys.",
    "Symmetry": "Symmetry",
    "Universe": "Universe",
    "Sensors": "Sensors",
    "Galaxies": "Galaxies",
    "International Journal of Modern Physics A": "Int. J. Mod. Phys. A",
    "International Journal of Modern Physics D": "Int. J. Mod. Phys. D",
    "Modern Physics Letters A": "Mod. Phys. Lett. A",
    "Nature": "Nature",
    "Nature Astronomy": "Nat. Astron.",
    "Nature Physics": "Nat. Phys.",
    "Science": "Science",
    "Science Advances": "Sci. Adv.",
    "Applied Optics": "Appl. Opt.",
    "Optics Express": "Opt. Express",
    "Optics Letters": "Opt. Lett.",
    "New Journal of Physics": "New J. Phys.",
    "Chinese Physics Letters": "Chin. Phys. Lett.",
    "Reports on Progress in Physics": "Rep. Prog. Phys.",
    "Annual Review of Astronomy and Astrophysics": "Annu. Rev. Astron. Astrophys.",
    "Frontiers in Physics": "Front. Phys.",
    "Results in Physics": "Results Phys.",
    # Additional journals (from Crossref container-title values)
    "Chinese Journal of Physics": "Chin. J. Phys.",
    "Advances in Space Research": "Adv. Space Res.",
    "Aerospace Science and Technology": "Aerosp. Sci. Technol.",
    "Acta Astronautica": "Acta Astronaut.",
    "Nuclear Physics B": "Nucl. Phys. B",
    "Physics of the Dark Universe": "Phys. Dark Universe",
    "Annals of Physics": "Ann. Phys.",
    "Gravitation and Cosmology": "Gravit. Cosmol.",
    "Plasma Science and Technology": "Plasma Sci. Technol.",
    "Journal of Physics: Conference Series": "J. Phys. Conf. Ser.",
    "Journal of Low Temperature Physics": "J. Low Temp. Phys.",
    "CEAS Space Journal": "CEAS Space J.",
    "Experimental Astronomy": "Exp. Astron.",
    "The European Physical Journal Plus": "Eur. Phys. J. Plus",
    "The European Physical Journal Special Topics": "Eur. Phys. J. Spec. Top.",
    "European Physical Journal Special Topics": "Eur. Phys. J. Spec. Top.",
    "Rendiconti Lincei. Scienze Fisiche e Naturali": "Rend. Lincei",
    "Chinese Journal of Space Science": "Chin. J. Space Sci.",
    "Scientia Sinica Physica, Mechanica & Astronomica": "Sci. Sin. Phys. Mech. Astron.",
    "Frontiers of Physics": "Front. Phys.",
    "Frontiers in Astronomy and Space Sciences": "Front. Astron. Space Sci.",
    "JCAP": "J. Cosmol. Astropart. Phys.",
    "Classical and Quantum Gravity": "Class. Quantum Grav.",
    "Journal of Cosmology and Astroparticle Physics": "J. Cosmol. Astropart. Phys.",
    "The European Physical Journal C - Particles and Fields": "Eur. Phys. J. C",
    "Measurement Science and Technology": "Meas. Sci. Technol.",
    "Applied Sciences": "Appl. Sci.",
    "Photonics": "Photonics",
    "Micromachines": "Micromachines",
    "Chinese Optics Letters": "Chin. Opt. Lett.",
    "Optics and Lasers in Engineering": "Opt. Lasers Eng.",
    "Review of Scientific Instruments": "Rev. Sci. Instrum.",
    "International Journal of Modern Physics D": "Int. J. Mod. Phys. D",
    "International Journal of Modern Physics A": "Int. J. Mod. Phys. A",
    "Modern Physics Letters A": "Mod. Phys. Lett. A",
    "Physical Review Applied": "Phys. Rev. Appl.",
    "Physical Review Accelerators and Beams": "Phys. Rev. Accel. Beams",
    "Progress in Particle and Nuclear Physics": "Prog. Part. Nucl. Phys.",
    "Physics Letters A": "Phys. Lett. A",
    "General Relativity and Gravitation": "Gen. Relativ. Gravit.",
    "The Astronomical Journal": "Astron. J.",
    "Publications of the Astronomical Society of the Pacific": "Publ. Astron. Soc. Pac.",
    "Communications in Theoretical Physics": "Commun. Theor. Phys.",
    "Science China Technological Sciences": "Sci. China Technol. Sci.",
    "Science China Information Sciences": "Sci. China Inf. Sci.",
    "Science China Earth Sciences": "Sci. China Earth Sci.",
    "Space: Science & Technology": "Space Sci. Technol.",
    "Advances in Astronomy": "Adv. Astron.",
    "Fortschritte der Physik": "Fortschr. Phys.",
    "Computer Physics Communications": "Comput. Phys. Commun.",
    "Physical Review C": "Phys. Rev. C",
    "Physical Review E": "Phys. Rev. E",
    "Proceedings of the Royal Society A: Mathematical, Physical and Engineering Sciences": "Proc. R. Soc. A",
    "AAPPS Bulletin": "AAPPS Bull.",
    "International Journal of Aerospace Engineering": "Int. J. Aerosp. Eng.",
    "Optics Communications": "Opt. Commun.",
    # HTML-entity variants returned by Crossref
    "Science China Physics, Mechanics &amp; Astronomy": "Sci. China Phys. Mech. Astron.",
    "Optics &amp; Laser Technology": "Opt. Laser Technol.",
    "Laser &amp; Optoelectronics Progress": "Laser Optoelectron. Prog.",
    "SCIENTIA SINICA Physica, Mechanica &amp; Astronomica": "Sci. Sin. Phys. Mech. Astron.",
    "Space: Science &amp; Technology": "Space Sci. Technol.",
    "Astronomy &amp; Astrophysics": "Astron. Astrophys.",
    # Top unmapped journals from Crossref
    "IEEE Transactions on Instrumentation and Measurement": "IEEE Trans. Instrum. Meas.",
    "Microgravity Science and Technology": "Microgravity Sci. Technol.",
    "Measurement": "Measurement",
    "Aerospace": "Aerospace",
    "Optics & Laser Technology": "Opt. Laser Technol.",
    "ACTA PHOTONICA SINICA": "Acta Photonica Sin.",
    "Acta Photonica Sinica": "Acta Photonica Sin.",
    "Chinese Journal of Aeronautics": "Chin. J. Aeronaut.",
    "Remote Sensing": "Remote Sens.",
    "IEEE Sensors Journal": "IEEE Sens. J.",
    "IEEE Transactions on Aerospace and Electronic Systems": "IEEE Trans. Aerosp. Electron. Syst.",
    "Vacuum": "Vacuum",
    "Optical Engineering": "Opt. Eng.",
    "Acta Physica Sinica": "Acta Phys. Sin.",
    "Space Weather": "Space Weather",
    "Applied Physics B": "Appl. Phys. B",
    "Communications Physics": "Commun. Phys.",
    "Journal of High Energy Astrophysics": "J. High Energy Astrophys.",
    "Electronics": "Electronics",
    "EPJ Web of Conferences": "EPJ Web Conf.",
    "Scientific Reports": "Sci. Rep.",
    "Sensors and Actuators A: Physical": "Sens. Actuators A",
    "Astronomische Nachrichten": "Astron. Nachr.",
    "Acta Mechanica Sinica": "Acta Mech. Sin.",
    "Infrared and Laser Engineering": "Infrared Laser Eng.",
    "Acta Optica Sinica": "Acta Opt. Sin.",
    "AIP Advances": "AIP Adv.",
    "Laser & Optoelectronics Progress": "Laser Optoelectron. Prog.",
    "Machine Learning: Science and Technology": "Mach. Learn. Sci. Technol.",
    "Fundamental Research": "Fundam. Res.",
    "npj Microgravity": "npj Microgravity",
    "Journal of Modern Optics": "J. Mod. Opt.",
    "Reviews of Modern Plasma Physics": "Rev. Mod. Plasma Phys.",
    "npj Space Exploration": "npj Space Explor.",
    "IEEE Photonics Journal": "IEEE Photonics J.",
    "IEEE Photonics Technology Letters": "IEEE Photonics Technol. Lett.",
    "Journal of Guidance, Control, and Dynamics": "J. Guid. Control Dyn.",
    "Journal of Optics": "J. Opt.",
    "Research": "Research",
    "SCIENTIA SINICA Physica, Mechanica & Astronomica": "Sci. Sin. Phys. Mech. Astron.",
    # Unmapped journals (from fix-journals dry run 2026-04-22)
    "Handbook of Gravitational Wave Astronomy": "Handb. Gravit. Wave Astron.",
    "Nature Reviews Physics": "Nat. Rev. Phys.",
    "Journal of Geophysical Research: Space Physics": "J. Geophys. Res. Space Phys.",
    "Philosophical Transactions of the Royal Society A: Mathematical, Physical and Engineering Sciences": "Philos. Trans. R. Soc. A",
    "Precision Engineering": "Precis. Eng.",
    "Acta Polytechnica": "Acta Polytech.",
    "SoftwareX": "SoftwareX",
    "Nuclear and Particle Physics Proceedings": "Nucl. Part. Phys. Proc.",
    "Physica Scripta": "Phys. Scr.",
    "Monthly Notices of the Royal Astronomical Society: Letters": "Mon. Not. R. Astron. Soc. Lett.",
    "The European Physical Journal D": "Eur. Phys. J. D",
    "Chinese Journal of Lasers": "Chin. J. Lasers",
    "APL Photonics": "APL Photonics",
    "Progress in Aerospace Sciences": "Prog. Aerosp. Sci.",
    "SciPost Physics Core": "SciPost Phys. Core",
    "Physics Today": "Phys. Today",
    "Infrared Physics & Technology": "Infrared Phys. Technol.",
    "Infrared Physics &amp; Technology": "Infrared Phys. Technol.",
    "Biomicrofluidics": "Biomicrofluidics",
    "Journal of Open Source Software": "J. Open Source Softw.",
    "Microwave and Optical Technology Letters": "Microw. Opt. Technol. Lett.",
    "Advances in Physics: X": "Adv. Phys. X",
    "International Journal of Extreme Manufacturing": "Int. J. Extrem. Manuf.",
    "Journal of Astronomical Telescopes, Instruments, and Systems": "J. Astron. Telesc. Instrum. Syst.",
    "Machines": "Machines",
    "IEEE Transactions on Automation Science and Engineering": "IEEE Trans. Autom. Sci. Eng.",
    "IEEE Access": "IEEE Access",
    "Journal of Zhejiang University-SCIENCE A": "J. Zhejiang Univ. Sci. A",
    "Physics of Plasmas": "Phys. Plasmas",
    "Springer Series in Astrophysics and Cosmology": "Springer Ser. Astrophys. Cosmol.",
    "SSRN Electronic Journal": "SSRN Electron. J.",
    "International Journal of Ambient Computing and Intelligence": "Int. J. Ambient Comput. Intell.",
    "Advances in Cosmology": "Adv. Cosmol.",
    "Compact Objects in the Universe": "Compact Objects Universe",
    "Recent Progress in Relativistic Astrophysics": "Recent Prog. Relativ. Astrophys.",
}

# Generic abbreviations that are publisher names, not specific journals.
# When DOI prefix matching returns one of these, we should prefer the journal
# name field instead.  Note: "Nature" and "Science" are NOT generic — they are
# both publisher names AND specific journal titles.
GENERIC_ABBREVS = {
    'Springer', 'Elsevier', 'IOP', 'MDPI', 'AAS', 'IEEE', 'AIP',
    'World Sci.', 'OUP', 'Optica', 'Wiley', 'EDP Sci.',
    'Front.', 'JETP', 'Cambridge Univ. Press', 'Phys. Rev.',
    'Eur. Phys. J.', 'Sci. Sin.',
}

# Sort DOI prefixes by length descending for longest-match-first
_SORTED_DOI_PREFIXES = sorted(DOI_PREFIX_ABBREV.keys(), key=len, reverse=True)


def get_journal_abbrev(doi: Optional[str], journal: Optional[str]) -> Optional[str]:
    """
    Resolve journal abbreviation from DOI prefix and/or journal name.

    Priority:
    1. DOI prefix match -> if specific (non-generic), return immediately
    2. journal field   -> lookup in JOURNAL_NAME_ABBREV
    3. journal field   -> return raw journal name (better than a generic publisher)
    4. Generic DOI prefix result (last resort)

    Args:
        doi: DOI string or None
        journal: Full journal name or None

    Returns:
        Journal abbreviation or None
    """
    doi_result = None

    # Try DOI prefix match (longest prefix wins)
    if doi:
        for prefix in _SORTED_DOI_PREFIXES:
            if doi.startswith(prefix):
                doi_result = DOI_PREFIX_ABBREV[prefix]
                break

    # If DOI gave a specific (non-generic) result, use it directly
    if doi_result and doi_result not in GENERIC_ABBREVS:
        return doi_result

    # Try journal name mapping
    if journal:
        if journal in JOURNAL_NAME_ABBREV:
            return JOURNAL_NAME_ABBREV[journal]
        # Case-insensitive match
        journal_lower = journal.lower()
        for name, abbrev in JOURNAL_NAME_ABBREV.items():
            if name.lower() == journal_lower:
                return abbrev
        # Journal name exists but has no mapping — return it as-is
        # (a real journal name is more informative than a generic publisher)
        return journal

    # Fall back to generic DOI prefix result (e.g. "Springer")
    if doi_result:
        return doi_result

    return None


def parse_date_from_entry(entry: Dict[str, Any]) -> str:
    """
    Parse a date from an entry. Priority:
    1. published_date field (pre-resolved by fix_dates.py)
    2. arXiv ID (YYMM.NNNNN → 20YY-MM-15)
    3. Fallback to YYYY-01-01

    Args:
        entry: Paper entry dictionary

    Returns:
        Date string in YYYY-MM-DD format
    """
    # Priority 1: pre-resolved published_date
    published_date = entry.get('published_date')
    if published_date and re.match(r'^\d{4}-\d{2}-\d{2}$', str(published_date)):
        return str(published_date)

    arxiv_id = entry.get('arxiv_id')
    year = entry.get('year', datetime.now().year)

    if arxiv_id:
        # Match arXiv ID format: YYMM.NNNNN or YYMM.NNNNNvN
        m = re.match(r'^(\d{2})(\d{2})\.\d+', str(arxiv_id))
        if m:
            yy = int(m.group(1))
            mm = int(m.group(2))
            # Convert 2-digit year: 00-99 → 2000-2099
            full_year = 2000 + yy
            if 1 <= mm <= 12:
                return f"{full_year:04d}-{mm:02d}-15"

    # Fallback: year only
    return f"{year}-01-01"


def yaml_safe_str(s: str) -> str:
    """
    Return a YAML-safe quoted string. Uses single quotes to avoid
    backslash escape interpretation (e.g. LaTeX \\mathcal).
    Internal single quotes are escaped by doubling them.
    """
    return "'" + s.replace("'", "''") + "'"


def generate_frontmatter(entry: Dict[str, Any]) -> str:
    """
    Generate Hugo frontmatter YAML from entry.

    Args:
        entry: Paper entry dictionary

    Returns:
        YAML frontmatter string
    """
    lines = ['---']

    # Title (use single quotes to avoid YAML backslash escape issues with LaTeX)
    title = entry.get('title', '')
    lines.append(f'title: {yaml_safe_str(title)}')

    # Date (parse from arXiv ID or fallback)
    date = parse_date_from_entry(entry)
    lines.append(f'date: {date}')

    # Authors
    lines.append('authors:')
    for author in entry.get('authors', []):
        lines.append(f'  - name: {yaml_safe_str(author.get("name", ""))}')
        if author.get('affiliation'):
            lines.append(f'    affiliation: {yaml_safe_str(author["affiliation"])}')

    # Journal info
    if entry.get('journal'):
        lines.append(f'journal: {yaml_safe_str(entry["journal"])}')
    if entry.get('volume'):
        lines.append(f'volume: {yaml_safe_str(entry["volume"])}')
    if entry.get('pages'):
        lines.append(f'pages: {yaml_safe_str(entry["pages"])}')

    # Journal abbreviation
    journal_abbrev = get_journal_abbrev(entry.get('doi'), entry.get('journal'))
    if journal_abbrev:
        lines.append(f'journal_abbrev: {yaml_safe_str(journal_abbrev)}')

    # Year
    year = entry.get('year', datetime.now().year)
    lines.append(f'year: {year}')

    # Identifiers
    if entry.get('arxiv_id'):
        lines.append(f'arxiv: {yaml_safe_str(entry["arxiv_id"])}')
    if entry.get('doi'):
        lines.append(f'doi: {yaml_safe_str(entry["doi"])}')

    # Keywords
    if entry.get('keywords'):
        lines.append('keywords:')
        for kw in entry['keywords']:
            lines.append(f'  - {yaml_safe_str(kw)}')

    # Abstract
    if entry.get('abstract'):
        abstract = entry['abstract'].replace('\n', '\n  ')
        lines.append('abstract: |')
        lines.append(f'  {abstract}')

    # Publication type
    pub_type = entry.get('publication_type', 'journal')
    lines.append(f'publication_type: {yaml_safe_str(pub_type)}')

    # Featured
    featured = entry.get('featured', False)
    lines.append(f'featured: {str(featured).lower()}')

    # Citation count (if available)
    citations = entry.get('citations', {})
    if citations.get('count', 0) > 0:
        lines.append(f'citation_count: {citations["count"]}')

    # Taiji Collaboration flag
    if entry.get('taiji_collaboration'):
        lines.append('taiji_collaboration: true')

    lines.append('---')

    return '\n'.join(lines)


def generate_content(entry: Dict[str, Any]) -> str:
    """
    Generate Hugo content body from entry.

    Args:
        entry: Paper entry dictionary

    Returns:
        Markdown content string
    """
    lines = []

    # Summary from abstract (first 200 chars)
    abstract = entry.get('abstract', '')
    if abstract:
        summary = abstract[:200].rsplit(' ', 1)[0] + '...' if len(abstract) > 200 else abstract
        lines.append(summary)

    return '\n'.join(lines)


def generate_filename(entry: Dict[str, Any]) -> str:
    """
    Generate filename for Hugo content file.

    Args:
        entry: Paper entry dictionary

    Returns:
        Filename string (without extension)
    """
    date_prefix = parse_date_from_entry(entry)

    # Generate slug from title
    title = entry.get('title', 'untitled')
    slug = title.lower()
    # Remove special characters
    slug = ''.join(c if c.isalnum() or c in ' -' else '' for c in slug)
    # Replace spaces with hyphens
    slug = '-'.join(slug.split())
    # Limit length
    slug = slug[:50].rstrip('-')

    return f"{date_prefix}-{slug}"


def sync_entry_to_hugo(entry: Dict[str, Any], output_dir: Path,
                       dry_run: bool = False) -> tuple[bool, str]:
    """
    Sync a single entry to Hugo content.

    Args:
        entry: Paper entry dictionary
        output_dir: Directory for Hugo content
        dry_run: If True, don't write files

    Returns:
        Tuple of (success, filename)
    """
    filename = generate_filename(entry)
    filepath = output_dir / f"{filename}.md"

    frontmatter = generate_frontmatter(entry)
    content = generate_content(entry)

    full_content = f"{frontmatter}\n\n{content}\n"

    if dry_run:
        logger.info(f"[DRY RUN] Would write: {filepath}")
        return True, filename

    try:
        filepath.write_text(full_content, encoding='utf-8')
        logger.info(f"Wrote: {filepath}")
        return True, filename
    except Exception as e:
        logger.error(f"Failed to write {filepath}: {e}")
        return False, filename


def sync_database_to_hugo(dry_run: bool = False,
                          clean: bool = False) -> Dict[str, Any]:
    """
    Sync entire database to Hugo content directory.

    Args:
        dry_run: If True, don't write files
        clean: If True, remove existing publication files first

    Returns:
        Summary dictionary
    """
    # Load database
    db = load_database(DATABASE_PATH)
    entries = get_all_entries(db)

    logger.info(f"Syncing {len(entries)} entries to Hugo content")

    # Ensure output directory exists
    HUGO_CONTENT_PATH.mkdir(parents=True, exist_ok=True)

    # Clean existing files if requested
    if clean and not dry_run:
        existing_files = list(HUGO_CONTENT_PATH.glob('*.md'))
        # Keep _index.md
        existing_files = [f for f in existing_files if f.name != '_index.md']
        for f in existing_files:
            f.unlink()
            logger.info(f"Removed: {f}")

    # Sync entries
    success_count = 0
    failed_count = 0
    filenames = []

    for entry in entries:
        success, filename = sync_entry_to_hugo(entry, HUGO_CONTENT_PATH, dry_run)
        if success:
            success_count += 1
            filenames.append(filename)
        else:
            failed_count += 1

    # Also update Hugo data file
    if not dry_run:
        hugo_data_file = HUGO_DATA_PATH / "papers.json"
        hugo_data_file.parent.mkdir(parents=True, exist_ok=True)

        # Create a simplified version for Hugo (preserve taiji_collaboration)
        hugo_data = {
            'metadata': db.get('metadata', {}),
            'entries': [{
                'entry_id': e.get('entry_id'),
                'title': e.get('title'),
                'authors': e.get('authors', []),
                'year': e.get('year'),
                'journal': e.get('journal'),
                'doi': e.get('doi'),
                'arxiv_id': e.get('arxiv_id'),
                'keywords': e.get('keywords', []),
                'publication_type': e.get('publication_type'),
                'featured': e.get('featured', False),
                'citation_count': e.get('citations', {}).get('count', 0),
                'classification': e.get('classification', {}),
                'published_date': e.get('published_date'),
                'taiji_collaboration': e.get('taiji_collaboration', False)
            } for e in entries]
        }

        hugo_data_file.write_text(
            json.dumps(hugo_data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        logger.info(f"Updated Hugo data file: {hugo_data_file}")

    return {
        'total': len(entries),
        'success': success_count,
        'failed': failed_count,
        'files': filenames,
        'dry_run': dry_run
    }


def main():
    parser = argparse.ArgumentParser(
        description='Sync database to Hugo content',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/sync_database.py
    python scripts/sync_database.py --dry-run
    python scripts/sync_database.py --clean
        """
    )

    parser.add_argument('--dry-run', action='store_true',
                        help="Show what would be done without making changes")
    parser.add_argument('--clean', action='store_true',
                        help="Remove existing publication files before sync")

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("SYNC DATABASE TO HUGO CONTENT")
    print("=" * 60 + "\n")

    result = sync_database_to_hugo(dry_run=args.dry_run, clean=args.clean)

    print("\n" + "─" * 60)
    print("SUMMARY")
    print("─" * 60)
    print(f"Total entries: {result['total']}")
    print(f"Successfully synced: {result['success']}")
    print(f"Failed: {result['failed']}")

    if result['dry_run']:
        print("\n[DRY RUN] No files were actually written")
    else:
        print(f"\n✅ Sync complete!")

    sys.exit(0 if result['failed'] == 0 else 1)


if __name__ == '__main__':
    main()
