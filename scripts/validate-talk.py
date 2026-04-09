#!/usr/bin/env python3
"""
Validate talk YAML frontmatter
"""

import os
import sys
import yaml
from pathlib import Path

REQUIRED_FIELDS = ['title', 'date', 'speaker', 'event', 'talk_type', 'keywords']
VALID_TYPES = ['conference', 'seminar', 'workshop', 'colloquium', 'public']

def validate_talk(file_path):
    """Validate a single talk file"""
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

    # Validate talk type
    if 'talk_type' in frontmatter:
        if frontmatter['talk_type'] not in VALID_TYPES:
            errors.append(f"Invalid talk_type in {file_path}. Must be one of: {VALID_TYPES}")

    # Validate speaker structure
    if 'speaker' in frontmatter:
        if not isinstance(frontmatter['speaker'], dict):
            errors.append(f"Speaker must be a dictionary in {file_path}")
        elif 'name' not in frontmatter['speaker']:
            errors.append(f"Speaker missing 'name' field in {file_path}")

    # Validate keywords
    if 'keywords' in frontmatter:
        if not isinstance(frontmatter['keywords'], list):
            errors.append(f"Keywords must be a list in {file_path}")

    return errors

def main():
    """Validate all talk files"""
    talks_dir = Path('content/talks')

    if not talks_dir.exists():
        print("No talks directory found")
        return 0

    all_errors = []
    file_count = 0

    for talk_file in talks_dir.glob('*.md'):
        if talk_file.name == '_index.md':
            continue

        file_count += 1
        errors = validate_talk(talk_file)
        if errors:
            all_errors.extend(errors)

    if all_errors:
        print(f"Validation failed with {len(all_errors)} error(s):")
        for error in all_errors:
            print(f"  - {error}")
        return 1
    else:
        print(f"✓ All {file_count} talk(s) validated successfully")
        return 0

if __name__ == '__main__':
    sys.exit(main())
