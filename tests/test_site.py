import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SLUGS = [
    'panel-installation', 'panel-removal', 'filter-installation', 'filter-removal',
    'auto-lifting-panel-function', 'sky-airflow', 'sky-airflow-demo', 'wide-flow',
    'dual-side-airflow', 'horizontal-swing-remote-control',
    'vertical-swing-remote-control', 'vertical-swing-app',
]


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tags = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def catalog(page):
    match = re.search(r'<script id="videoCatalog" type="application/json">(.*?)</script>', page, re.S)
    return json.loads(match[1]) if match else None


class PublishedSiteTests(unittest.TestCase):
    def test_routes_expose_the_product_catalog(self):
        for slug in SLUGS:
            data = catalog((ROOT / slug / 'index.html').read_text())
            self.assertIsNotNone(data, f'{slug} has no catalog for in-page switching')
            self.assertEqual([item['slug'] for item in data['topics']], SLUGS)

    def test_real_build_preserves_media_and_is_repeatable(self):
        self.assertTrue((ROOT / 'build_pages.py').is_file(), 'cover/site builder is missing')
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / 'source'
            fixture.mkdir()
            for name in ['build_pages.py', 'player.js', 'sw-template.js', 'brand-logo.png']:
                shutil.copyfile(ROOT / name, fixture / name)
            for slug in SLUGS:
                shutil.copytree(ROOT / slug, fixture / slug)
            # A preview is commonly built inside the checkout. It must not be
            # mistaken for a thirteenth topic during the next build.
            first = fixture / 'dist'
            subprocess.run(['python3', str(fixture / 'build_pages.py'), str(first)], check=True, capture_output=True)
            versions = set()
            for slug in SLUGS:
                page = (first / slug / 'index.html').read_text()
                data = catalog(page)
                self.assertIsNotNone(data)
                versions.add(data['version'])
                self.assertEqual(len(re.findall('id="videoCatalog"', page)), 1)
                self.assertEqual([x['slug'] for x in data['topics']], SLUGS)
                self.assertIn('<title>TCL One-Way Cassette | ', page)
                tags = Page(page).tags
                links = [a for tag, a in tags if tag == 'a' and a.get('class') == 'video-link']
                self.assertEqual([a['href'] for a in links], ['../' + x + '/' for x in SLUGS])
                video = next(a for tag, a in tags if tag == 'video')
                self.assertEqual(video['preload'], 'auto')
                self.assertIn('playsinline', video)
                self.assertEqual(video['crossorigin'], 'anonymous')
                self.assertTrue(any(tag == 'img' and a.get('src', '').startswith('data:image/jpeg;base64,') for tag, a in tags))
                item = next(x for x in data['topics'] if x['slug'] == slug)
                original = (fixture / slug / (slug + '.mp4')).read_bytes()
                generated = (first / slug / (slug + '.mp4')).read_bytes()
                self.assertEqual(original, generated)
                self.assertEqual(item['hash'], hashlib.sha256(original).hexdigest())
                self.assertTrue((first / item['cover']).is_file())
                self.assertTrue(any(tag == 'source' and a.get('src') == item['file'].split('/')[-1] for tag, a in tags))
                script = re.findall(r'<script>\s*(.*?)</script>', page, re.S)[0]
                subprocess.run(['node', '--check'], input=script, text=True, capture_output=True, check=True)
                shutil.copyfile(first / slug / 'index.html', fixture / slug / 'index.html')
            self.assertEqual(len(versions), 1)
            subprocess.run(['node', '--check', str(first / 'sw.js')], check=True, capture_output=True)
            home = (first / 'index.html').read_text()
            self.assertIn('<h1>', home)
            self.assertNotIn('id="trainingVideo"', home)
            self.assertIn('./panel-installation/', home)
            self.assertEqual((first / 'brand-logo.png').read_bytes(), (fixture / 'brand-logo.png').read_bytes())
            second = Path(temporary) / 'second'
            rebuilt = subprocess.run(['python3', str(fixture / 'build_pages.py'), str(second)], text=True, capture_output=True)
            self.assertEqual(rebuilt.returncode, 0, rebuilt.stderr)
            first_files = {p.relative_to(first): p.read_bytes() for p in first.rglob('*') if p.is_file()}
            second_files = {p.relative_to(second): p.read_bytes() for p in second.rglob('*') if p.is_file()}
            self.assertEqual(first_files, second_files)


if __name__ == '__main__':
    unittest.main()
