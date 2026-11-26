"""Configure the generated preview only; no modification of the web source."""
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

root = Path(__file__).resolve().parent.parent
app = root / 'android/app'
manifest = app / 'src/main/AndroidManifest.xml'
text = manifest.read_text(encoding='utf-8')
# Disable Android's standard automatic backup for salary/leave data.
text, count = re.subn(r'android:allowBackup="(?:true|false)"', 'android:allowBackup="false"', text)
if count == 0:
    text, count = re.subn(r'<application\b', '<application android:allowBackup="false"', text, count=1)
assert count == 1, 'Unexpected Android manifest template'
ET.fromstring(text)
manifest.write_text(text, encoding='utf-8')

version = int(sys.argv[1]) if len(sys.argv) > 1 else 1
assert 0 < version < 2_100_000_000
build = app / 'build.gradle'
text = build.read_text(encoding='utf-8')
text, c = re.subn(r'(?m)^(\s*versionCode\s+)\d+\s*$', rf'\g<1>{version}', text)
assert c == 1, 'Unexpected versionCode template'
text, c = re.subn(r'(?m)^(\s*versionName\s+)["\'][^"\']+["\']\s*$', rf'\g<1>"0.1.0-preview.{version}"', text)
assert c == 1, 'Unexpected versionName template'
build.write_text(text, encoding='utf-8')
print(f'Android preview version 0.1.0-preview.{version}; standard backup disabled')
