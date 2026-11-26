"""Release-only preparation. Never changes www/. Run configure before cap add."""
import json
import re
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_ID = 'io.github.mragasferon.vacationplus'
PREVIEW_ID = APP_ID + '.preview'
INJECT = '<script src="./vacation-updates.js"></script>\n'

def version_code(version):
    if not re.fullmatch(r'(0|[1-9][0-9]{0,3})\.(0|[1-9][0-9]{0,2})\.(0|[1-9][0-9]{0,2})', version):
        raise ValueError('Version must be X.Y.Z, without leading zeroes; Y/Z <= 999')
    major, minor, patch = map(int, version.split('.'))
    code = major * 1_000_000 + minor * 1_000 + patch
    if not 0 < code <= 2_100_000_000:
        raise ValueError('Version code out of range')
    return code

def configure():
    path = ROOT / 'capacitor.config.json'
    cfg = json.loads(path.read_text(encoding='utf-8'))
    assert cfg['appId'] == PREVIEW_ID
    assert not cfg.get('server', {}).get('url')
    cfg.update(appId=APP_ID, appName='Отпуск × деньги')
    path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def prepare(version):
    code = version_code(version)
    subprocess.run([sys.executable, str(ROOT/'scripts/prepare-android.py'), str(code)], check=True)
    app = ROOT / 'android/app'
    gradle = app/'build.gradle'
    text, n = re.subn(r'(?m)^(\s*versionName\s+)"[^"\n]+"\s*$', rf'\g<1>"{version}"', gradle.read_text(encoding='utf-8'))
    assert n == 1
    gradle.write_text(text, encoding='utf-8')
    java = app/'src/main/java'/APP_ID.replace('.', '/')
    main = java/'MainActivity.java'
    text = main.read_text(encoding='utf-8')
    anchor = 'registerPlugin(VacationFilesPlugin.class);'
    assert text.count(anchor) == 1
    main.write_text(text.replace(anchor, anchor+'\n        registerPlugin(VacationUpdatesPlugin.class);'), encoding='utf-8')
    source = (ROOT/'android-src/VacationUpdatesPlugin.java').read_text(encoding='utf-8')
    (java/'VacationUpdatesPlugin.java').write_text(source, encoding='utf-8')
    public = app/'src/main/assets/public'
    html = (public/'index.html').read_bytes()
    assert html == (ROOT/'www/index.html').read_bytes()
    assert html.count(b'</body>') == 1
    (public/'index.html').write_bytes(html.replace(b'</body>', INJECT.encode()+b'</body>'))
    (public/'vacation-updates.js').write_bytes((ROOT/'android-src/vacation-updates.js').read_bytes())
    print(f'Production Android {version} ({code}) prepared')

if __name__ == '__main__':
    command = sys.argv[1]
    if command == 'code': print(version_code(sys.argv[2]))
    elif command == 'configure': configure()
    elif command == 'prepare': prepare(sys.argv[2])
    else: raise SystemExit('Unknown command')
