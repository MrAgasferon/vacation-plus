"""Refuse reuse or downgrade of an already tagged release."""
import re
import sys
from pathlib import Path
import runpy
version_code = runpy.run_path(str(Path(__file__).with_name('prepare-release.py')))['version_code']
version = sys.argv[1]
code = version_code(version)
for line in sys.stdin:
    tag = line.strip().split()[-1] if line.strip() else ''
    if not tag.startswith('refs/tags/v'):
        continue
    try:
        existing = version_code(tag.removeprefix('refs/tags/v'))
    except ValueError:
        continue
    if existing >= code:
        raise SystemExit(f'Use a higher version: existing {tag}')
print(f'Version {version} accepted ({code})')
