"""Generate static Pages assets and small covers, preserving original MP4 bytes."""
import base64
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
COVER = '<!-- VIDEO_COVER -->'


def digest_file(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def read_cover(video):
    for seek in ('0.15', '0'):
        result = subprocess.run(
            ['ffmpeg', '-nostdin', '-v', 'error', '-ss', seek, '-i', str(video),
             '-map', '0:v:0', '-frames:v', '1', '-vf', 'scale=480:-2',
             '-c:v', 'mjpeg', '-q:v', '8', '-threads', '1',
             '-f', 'image2pipe', 'pipe:1'],
            check=False, capture_output=True, timeout=60,
        )
        if result.returncode == 0 and result.stdout.startswith(b'\xff\xd8'):
            return result.stdout
    raise RuntimeError('Could not extract cover: ' + str(video.relative_to(ROOT)))


def normalize_template(page):
    # Published HTML is also the input template: rebuilding must not accumulate
    # scripts, catalogs, covers or content-version query strings.
    page = re.sub(r'\s*<script\b[^>]*>.*?</script>', '', page, flags=re.S)
    page = re.sub(r'(\.mp4)\?v=[0-9a-f]+', r'\1', page)
    page = re.sub(r'(brand-logo\.png)\?v=[0-9a-f]+', r'\1', page)
    page, count = re.subn(
        r'(<button\b(?=[^>]*\bid="videoPreview")[^>]*>).*?(</button>)',
        lambda m: m[1] + COVER + '<span aria-hidden="true">&#9654;</span>' + m[2],
        page, count=1, flags=re.S,
    )
    if count != 1:
        raise ValueError('Expected one initial preview button per topic.')
    page = re.sub(r'(<video\b)([^>]*)(>)', lambda m:
                  m[0] if re.search(r'\bcrossorigin=', m[2]) else
                  m[1] + ' crossorigin="anonymous"' + m[2] + m[3], page, count=1)
    return page.strip() + '\n'


def build(destination):
    paths = sorted(p for p in ROOT.glob('*/index.html')
                   if (p.parent / (p.parent.name + '.mp4')).is_file())
    templates = {p.parent.name: normalize_template(p.read_text()) for p in paths}
    if not templates:
        raise ValueError('No video pages found.')
    first = next(iter(templates.values()))
    links = re.findall(r'<a class="video-link" href="../([^/]+)/"[^>]*>(.*?)</a>', first)
    slugs = [slug for slug, _ in links]
    if len(slugs) != len(set(slugs)) or set(slugs) != set(templates):
        raise ValueError('The topic directory and video pages must match.')
    player = (ROOT / 'player.js').read_text()
    worker = (ROOT / 'sw-template.js').read_text()
    destination = destination.resolve()
    in_place = destination == ROOT
    if destination.exists() and any(destination.iterdir()) and not in_place:
        raise ValueError('Use an empty output directory, or --in-place.')
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'covers').mkdir(exist_ok=True)
    if not in_place:
        shutil.copyfile(ROOT / 'brand-logo.png', destination / 'brand-logo.png')
    logo_version = digest_file(ROOT / 'brand-logo.png')[:16]
    assets = ['brand-logo.png?v=' + logo_version]
    topics = []
    for slug, title in links:
        video = ROOT / slug / (slug + '.mp4')
        if not video.is_file():
            raise ValueError('Missing original video: ' + str(video.relative_to(ROOT)))
        media_hash = digest_file(video)
        image = read_cover(video)
        cover = 'covers/' + slug + '.' + hashlib.sha256(image).hexdigest()[:16] + '.jpg'
        (destination / cover).write_bytes(image)
        topics.append({
            'slug': slug, 'title': html.unescape(title),
            'file': slug + '/' + video.name + '?v=' + media_hash[:16],
            'hash': media_hash, 'bytes': video.stat().st_size, 'cover': cover,
        })
        assets.append(cover)
    version_input = player + worker + Path(__file__).read_text() + logo_version
    version_input += json.dumps(topics, sort_keys=True) + ''.join(templates.values())
    version = hashlib.sha256(version_input.encode()).hexdigest()[:16]

    def attach_player(page, root):
        catalog = {'version': version, 'root': root, 'topics': topics}
        data = json.dumps(catalog, ensure_ascii=False).replace('<', r'\u003c')
        scripts = '<script id="videoCatalog" type="application/json">' + data + '</script>\n'
        scripts += '<script>\n' + player + '</script>\n'
        page = page.replace('</body>', scripts + '</body>')
        return page.replace('brand-logo.png"', 'brand-logo.png?v=' + logo_version + '"')

    for item in topics:
        slug = item['slug']
        page = templates[slug]
        image = base64.b64encode((destination / item['cover']).read_bytes()).decode()
        page = page.replace(COVER, '<img src="data:image/jpeg;base64,' + image + '" alt="">')
        page = page.replace(slug + '.mp4"', slug + '.mp4?v=' + item['hash'][:16] + '"')
        target = destination / slug
        target.mkdir(exist_ok=True)
        (target / 'index.html').write_text(attach_player(page, '../'))
        if not in_place:
            shutil.copyfile(ROOT / slug / (slug + '.mp4'), target / (slug + '.mp4'))

    home, count = re.subn(
        r'<div class="video-container">.*?(?=<nav class="video-directory")',
        '', first, count=1, flags=re.S,
    )
    if count != 1:
        raise ValueError('Could not derive the product directory page.')
    home = re.sub(r'<title>.*?</title>', '<title>TCL One-Way Cassette | Operation Videos</title>', home, count=1, flags=re.S)
    home = re.sub(r'(<div class="video-title">).*?(</div>)', r'\1Operation Videos\2', home, count=1, flags=re.S)
    home = home.replace('../', './').replace(' aria-current="page"', '')
    (destination / 'index.html').write_text(attach_player(home, './'))
    config = {
        'version': version, 'pages': ['./'] + [slug + '/' for slug in slugs],
        'assets': assets,
        'videos': [{'url': x['file'], 'bytes': x['bytes'], 'hash': x['hash']} for x in topics],
    }
    (destination / 'sw.js').write_text(worker.replace('__CACHE_CONFIG__', json.dumps(config, separators=(',', ':'))))
    (destination / '.nojekyll').touch()
    print('Built ' + str(len(topics)) + ' topics, version ' + version + '; original MP4 files unchanged.')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python3 build_pages.py OUTPUT_DIRECTORY | --in-place')
    build(ROOT if sys.argv[1] == '--in-place' else Path(sys.argv[1]))
