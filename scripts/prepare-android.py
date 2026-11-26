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
# Keep the WebView resizable when the system keyboard is shown.
def adjust_keyboard(match):
    tag = match.group(0)
    if 'android:windowSoftInputMode=' in tag:
        return re.sub(r'android:windowSoftInputMode="[^"]+"', 'android:windowSoftInputMode="adjustResize"', tag)
    return (tag[:-2].rstrip() + ' android:windowSoftInputMode="adjustResize"/>') if tag.endswith('/>') else (tag[:-1] + ' android:windowSoftInputMode="adjustResize">')
text, count = re.subn(r'<activity\b[^>]*>', adjust_keyboard, text, count=1)
assert count == 1, 'Unexpected activity template'
# Reference unique resource names, not the Capacitor template launcher.
def configure_application(match):
    tag = match.group(0)
    for name,value in {'icon':'@mipmap/vacation_launcher','roundIcon':'@mipmap/vacation_launcher_round'}.items():
        pattern = rf'android:{name}="[^"]*"'
        if re.search(pattern,tag):
            tag = re.sub(pattern,f'android:{name}="{value}"',tag)
        else:
            tag = tag[:-1] + f' android:{name}="{value}">'
    return tag
text, count = re.subn(r'<application\b[^>]*>', configure_application, text, count=1)
assert count == 1
ET.fromstring(text)
manifest.write_text(text, encoding='utf-8')

version = int(sys.argv[1]) if len(sys.argv) > 1 else 1
assert 0 < version < 2_100_000_000
build = app / 'build.gradle'
text = build.read_text(encoding='utf-8')
text, c = re.subn(r'(?m)^(\s*versionCode\s+)\d+\s*$', rf'\g<1>{version}', text)
assert c == 1, 'Unexpected versionCode template'
text, c = re.subn(r'(?m)^(\s*versionName\s+)["\'][^"\']+["\']\s*$', rf'\g<1>"0.2.1-preview.{version}"', text)
assert c == 1, 'Unexpected versionName template'
build.write_text(text, encoding='utf-8')
print(f'Android preview version 0.2.1-preview.{version}; standard backup disabled')

# Native Java source is versioned; the rest of Android stays generated in CI.
from shutil import copyfile
from PIL import Image
java = app / 'src/main/java/io/github/mragasferon/vacationplus/preview'
assert (java / 'MainActivity.java').exists(), 'Unexpected package path'
for name in ('MainActivity.java', 'VacationFilesPlugin.java'):
    copyfile(root / 'android-src' / name, java / name)

res = app / 'src/main/res'
icon = Image.open(root / 'www/assets/icon-512.png').convert('RGBA')
mask = Image.open(root / 'www/assets/icon-maskable-512.png').convert('RGBA')
for density, size in {'mdpi':48,'hdpi':72,'xhdpi':96,'xxhdpi':144,'xxxhdpi':192}.items():
    folder = res / ('mipmap-' + density)
    folder.mkdir(exist_ok=True)
    for name in ('vacation_launcher','vacation_launcher_round'):
        icon.resize((size,size),Image.Resampling.LANCZOS).save(folder / (name+'.png'))
    mask.resize((int(size*2.25),int(size*2.25)),Image.Resampling.LANCZOS).save(folder/'vacation_launcher_foreground.png')
# Explicit adaptive launcher resources, no template foreground left over.
anydpi = res / 'mipmap-anydpi-v26'; anydpi.mkdir(exist_ok=True)
for name in ('vacation_launcher','vacation_launcher_round'):
    (anydpi / (name+'.xml')).write_text('''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/vacation_background" />
    <foreground android:drawable="@mipmap/vacation_launcher_foreground" />
</adaptive-icon>''',encoding='utf-8')
(res/'values/vacation_colors.xml').write_text('<resources><color name="vacation_background">#0B1020</color></resources>',encoding='utf-8')
# Reuse the native Android 12+ splash theme from Capacitor (AndroidX backport for older OS).
folder=res/'drawable-nodpi'; folder.mkdir(exist_ok=True)
icon.resize((288,288),Image.Resampling.LANCZOS).save(folder/'vacation_splash_icon.png')
for styles in res.glob('values*/styles.xml'):
    tree=ET.parse(styles); node=tree.getroot().find("style[@name='AppTheme.NoActionBarLaunch']")
    if node is None: continue
    if 'SplashScreen' in node.get('parent',''):
        for name,value in {'windowSplashScreenBackground':'@color/vacation_background','windowSplashScreenAnimatedIcon':'@drawable/vacation_splash_icon'}.items():
            for item in list(node.findall('item')):
                if item.get('name')==name: node.remove(item)
            ET.SubElement(node,'item',{'name':name}).text=value
        tree.write(styles,encoding='utf-8',xml_declaration=True)
# Legacy splash drawable sizes use the template's existing aspect ratios.
for splash in res.glob('drawable*/splash.png'):
    with Image.open(splash) as source: w,h=source.size
    canvas=Image.new('RGBA',(w,h),'#0b1020'); size=max(1,int(min(w,h)*.35))
    canvas.alpha_composite(icon.resize((size,size),Image.Resampling.LANCZOS),((w-size)//2,(h-size)//2)); canvas.convert('RGB').save(splash)
print('Native files and launcher/splash resources configured')
