"""Stamp only the staged Pages artifact, never the tracked web source or APK."""
import re
import sys
from pathlib import Path

revision, filename = sys.argv[1:]
if not re.fullmatch(r"[a-f0-9]{40,64}", revision):
    raise SystemExit("Invalid web tree revision")
p = Path(filename)
html = p.read_bytes()
marker = b'<meta name="vacation-build" content="dev">'
if html.count(marker) != 1:
    raise SystemExit("Expected exactly one vacation-build marker")
p.write_bytes(html.replace(marker, marker.replace(b'"dev"', b'"' + revision.encode() + b'"')))
