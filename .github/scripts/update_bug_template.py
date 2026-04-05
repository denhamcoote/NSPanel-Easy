#!/usr/bin/env python3
# .github/scripts/update_bug_template.py
#
# Updates version placeholder values in the GitHub bug report template
# (.github/ISSUE_TEMPLATE/bug.yml) without reformatting the file.
#
# Called by the versioning workflow on every release to keep the placeholder
# hints in sync with the current release versions.
#
# Usage:
#   python3 update_bug_template.py <template> <tft> <firmware> <blueprint>
#
# Arguments:
#   template   Path to the bug report template YAML file.
#   tft        Minimum required TFT version (e.g. "15").
#   firmware   Current ESPHome firmware version (e.g. "2026.4.2").
#   blueprint  Minimum required Blueprint version (e.g. "2026.4.2").
#
# Each placeholder is located by the label that precedes it, making the
# update index-independent and safe against future template reordering.

import re
import sys


def update_placeholder(content: str, label: str, value: str) -> tuple[str, int]:
    """Replace the placeholder value following a given label field.

    Matches the label and the next placeholder: line using MULTILINE mode
    with line anchors, replacing only the value after 'e.g., '.
    Does NOT use DOTALL — the trailing match is restricted to non-newline
    characters to avoid consuming content beyond the target line.

    Args:
        content: Full file content as a string.
        label:   The label text to anchor the search (e.g. 'TFT Version').
        value:   The new placeholder value to set.

    Returns:
        Tuple of (updated content, number of replacements made).
        Returns (content, 0) if the label is not found.
    """
    pattern = (
        r'(^\s*label:\s*' + re.escape(label) +
        r'\s*$[\s\S]*?\s*placeholder:\s*)e\.g\.,[ \t]*[^\n\r]*'
    )
    replacement = r'\g<1>e.g., ' + value
    updated, count = re.subn(
        pattern,
        replacement,
        content,
        count=1,
        flags=re.MULTILINE,
    )
    return updated, count


def main() -> None:
    if len(sys.argv) != 5:
        print(
            f'Usage: {sys.argv[0]} <template> <tft> <firmware> <blueprint>',
            file=sys.stderr,
        )
        sys.exit(1)

    template_path = sys.argv[1]
    tft_version = sys.argv[2]
    firmware_version = sys.argv[3]
    blueprint_version = sys.argv[4]

    with open(template_path, encoding='utf-8') as f:
        content = f.read()

    replacements = [
        ('TFT Version', tft_version),
        ('Firmware Version', firmware_version),
        ('Blueprint Version', blueprint_version),
    ]

    errors = []
    for label, value in replacements:
        content, count = update_placeholder(content, label, value)
        if count != 1:
            errors.append(
                f"  '{label}': expected 1 replacement, got {count}"
            )

    if errors:
        print('ERROR: placeholder update failed:', file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        print(
            'Check that the label names in the template have not been renamed.',
            file=sys.stderr,
        )
        sys.exit(2)

    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f'Updated placeholders in {template_path}:')
    print(f'  TFT Version:       e.g., {tft_version}')
    print(f'  Firmware Version:  e.g., {firmware_version}')
    print(f'  Blueprint Version: e.g., {blueprint_version}')


if __name__ == '__main__':
    main()
