#!/usr/bin/env python3
"""
Validate publication YAML frontmatter
"""

import os
import sys
import yaml
from pathlib import Path

REQUIRED_FIELDS = ['title', 'date', 'authors', 'year', 'keywords', 'publication_type']
VALID_TYPES = ['journal', 'conference', 'preprint']

def validate_publication(file_path):
    """Validate a single publication file"""
    errors = []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract frontmatter
    if not content.startswith('---'):
        errors.append(f"Missing frontmatter in {file_path}")
        return errors

    parts = content.split('---', 2)
    if len(parts) < 3:
        errors.append(f"Invalid frontmatter format in {file_path}")
        return errors

    try:
        frontmatter = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        errors.append(f"YAML parsing error in {file_path}: {e}")
        return errors

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in frontmatter or not frontmatter[field]:
            errors.append(f"Missing required field '{field}' in {file_path}")

    # Validate publication type
    if 'publication_type' in frontmatter:
        if frontmatter['publication_type'] not in VALID_TYPES:
            errors.append(f"Invalid publication_type in {file_path}. Must be one of: {VALID_TYPES}")

    # Validate authors structure
    if 'authors' in frontmatter:
        if not isinstance(frontmatter['authors'], list):
            errors.append(f"Authors must be a list in {file_path}")
        else:
            for i, author in enumerate(frontmatter['authors']):
                if not isinstance(author, dict) or 'name' not in author:
                    errors.append(f"Author {i} missing 'name' field in {file_path}")

    # Validate keywords
    if 'keywords' in frontmatter:
        if not isinstance(frontmatter['keywords'], list):
            errors.append(f"Keywords must be a list in {file_path}")

    return errors

def main():
    """Validate all publication files"""
    publications_dir = Path('content/publications')

    if not publications_dir.exists():
        print("No publications directory found")
        return 0

    all_errors = []
    file_count = 0

    for pub_file in publications_dir.glob('*.md'):
        if pub_file.name == '_index.md':
            continue

        file_count += 1
        errors = validate_publication(pub_file)
        if errors:
            all_errors.extend(errors)

    if all_errors:
        print(f"Validation failed with {len(all_errors)} error(s):")
        for error in all_errors:
            print(f"  - {error}")
        return 1
    else:
        print(f"✓ All {file_count} publication(s) validated successfully")
        return 0

if __name__ == '__main__':
    sys.exit(main())
