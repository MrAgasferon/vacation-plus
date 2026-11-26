import json
import runpy
import sys
from pathlib import Path
from zipfile import ZipFile

version, apk, badging_file, resources_file = sys.argv[1:]
helpers = runpy.run_path(str(Path(__file__).with_name('prepare-release.py')))
app_id, code, inject = helpers['APP_ID'], helpers['version_code'](version), helpers['INJECT']
badging = Path(badging_file).read_text(encoding='utf-8')
package_line = next(line for line in badging.splitlines() if line.startswith('package:'))
for expected in (f"name='{app_id}'", f"versionCode='{code}'", f"versionName='{version}'"):
    assert expected in package_line, (expected, package_line)
assert 'application-debuggable' not in badging
resources = Path(resources_file).read_text(encoding='utf-8')
for name in ('vacation_launcher', 'vacation_launcher_round', 'vacation_launcher_foreground'):
    assert 'mipmap/'+name in resources, name
with ZipFile(apk) as archive:
    for path in Path('www').rglob('*'):
        if path.is_file():
            name = 'assets/public/' + path.relative_to('www').as_posix()
            expected = path.read_bytes()
            if path == Path('www/index.html'):
                expected = expected.replace(b'</body>', inject.encode()+b'</body>')
            assert archive.read(name) == expected, name
    assert archive.read('assets/public/vacation-updates.js') == Path('android-src/vacation-updates.js').read_bytes()
    config = json.loads(archive.read('assets/capacitor.config.json'))
    assert config['appId'] == app_id
    assert not config.get('server', {}).get('url')
print('Production package, version, launcher, offline resources and release mode verified')
