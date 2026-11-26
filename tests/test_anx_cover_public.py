"""Public reading stats must not hand out the ebook that sits next to the cover."""

import os
import sys
import tempfile
import types
import unittest


ROOT = tempfile.mkdtemp(prefix='anx-cover-')
os.environ['CONFIG_DIR'] = os.path.join(ROOT, 'config')
os.environ['WEBDAV_DIR'] = os.path.join(ROOT, 'webdav')
os.environ['LOG_DIR'] = os.path.join(ROOT, 'logs')
os.makedirs(os.environ['CONFIG_DIR'], exist_ok=True)
os.makedirs(os.environ['LOG_DIR'], exist_ok=True)

PROJECT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)


def _stub(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


# The cover route never touches ebook parsers. Stub them so this test can
# import the blueprint without Pillow, ebooklib, or the rest of that stack.
_stub('ebookmeta')
_pil = _stub('PIL')
_pil.Image = _stub('PIL.Image')
_pil.ImageDraw = _stub('PIL.ImageDraw')
_pil.ImageFont = _stub('PIL.ImageFont')
_ebooklib = _stub('ebooklib')
_ebooklib.epub = _stub('ebooklib.epub', EpubBook=object, read_epub=lambda *args, **kwargs: None)
_stub('mobi_header', MobiHeader=object)
_stub('pypdf', PdfReader=object)
_stub('bs4', BeautifulSoup=object)
_lxml = _stub('lxml')
_lxml.etree = _stub('lxml.etree')
_lxml.html = _stub('lxml.html')

from flask import Flask, g, request  # noqa: E402

import database  # noqa: E402
from blueprints.main import main_bp  # noqa: E402
from utils.anx_cover_path import is_anx_cover_relpath  # noqa: E402

JPEG = b'\xff\xd8\xffFAKEJPEG'
EPUB = b'EPUB-SECRET-BYTES'


class AnxCoverPublicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database.create_schema()
        db = database.get_db()
        db.execute(
            'INSERT INTO users (username, password_hash, role, stats_public) VALUES (?, ?, ?, ?)',
            ('alice', 'not-a-real-hash', 'user', 1),
        )
        db.close()

        data = os.path.join(os.environ['WEBDAV_DIR'], 'alice', 'anx', 'data')
        os.makedirs(os.path.join(data, 'cover'), exist_ok=True)
        os.makedirs(os.path.join(data, 'file'), exist_ok=True)
        with open(os.path.join(data, 'cover', 'book.jpg'), 'wb') as handle:
            handle.write(JPEG)
        with open(os.path.join(data, 'file', 'book.epub'), 'wb') as handle:
            handle.write(EPUB)

        cls.app = Flask(__name__)
        cls.app.register_blueprint(main_bp)

        class _Owner:
            id = 1
            username = 'alice'

        @cls.app.before_request
        def _user():
            # The signed-in cover route is the only one that should see an owner.
            own_cover = request.path.startswith('/anx_cover/') and not request.path.startswith('/anx_cover_public/')
            g.user = _Owner() if own_cover else None

        cls.client = cls.app.test_client()

    def test_helper_accepts_only_cover_images(self):
        self.assertTrue(is_anx_cover_relpath('cover/book.jpg'))
        self.assertTrue(is_anx_cover_relpath('cover/book.JPEG'))
        self.assertFalse(is_anx_cover_relpath('file/book.epub'))
        self.assertFalse(is_anx_cover_relpath('cover/../file/book.epub'))
        self.assertFalse(is_anx_cover_relpath('cover/book.epub'))
        self.assertFalse(is_anx_cover_relpath('/etc/passwd'))
        self.assertFalse(is_anx_cover_relpath(''))

    def test_public_cover_is_served_when_stats_are_public(self):
        response = self.client.get('/anx_cover_public/alice/cover/book.jpg')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, JPEG)

    def test_public_stats_do_not_serve_the_ebook(self):
        response = self.client.get('/anx_cover_public/alice/file/book.epub')
        self.assertNotEqual(response.status_code, 200)
        self.assertNotIn(EPUB, response.data)

    def test_public_stats_do_not_follow_a_cover_path_out_of_the_cover_dir(self):
        response = self.client.get('/anx_cover_public/alice/cover/../file/book.epub')
        self.assertNotIn(EPUB, response.data)

    def test_public_stats_do_not_follow_a_cover_symlink_to_the_ebook(self):
        cover_dir = os.path.join(os.environ['WEBDAV_DIR'], 'alice', 'anx', 'data', 'cover')
        ebook = os.path.join(os.environ['WEBDAV_DIR'], 'alice', 'anx', 'data', 'file', 'book.epub')
        link = os.path.join(cover_dir, 'linked.jpg')
        os.symlink(ebook, link)
        try:
            response = self.client.get('/anx_cover_public/alice/cover/linked.jpg')
            self.assertNotEqual(response.status_code, 200)
            self.assertNotIn(EPUB, response.data)
        finally:
            os.unlink(link)

    def test_signed_in_cover_route_serves_the_cover_but_not_the_ebook(self):
        cover = self.client.get('/anx_cover/cover/book.jpg')
        self.assertEqual(cover.status_code, 200)
        self.assertEqual(cover.data, JPEG)
        ebook = self.client.get('/anx_cover/file/book.epub')
        self.assertNotEqual(ebook.status_code, 200)
        self.assertNotIn(EPUB, ebook.data)

    def test_private_stats_do_not_serve_the_cover_either(self):
        db = database.get_db()
        db.execute('UPDATE users SET stats_public = 0 WHERE username = ?', ('alice',))
        db.close()
        try:
            response = self.client.get('/anx_cover_public/alice/cover/book.jpg')
            self.assertNotEqual(response.status_code, 200)
            self.assertNotIn(JPEG, response.data)
        finally:
            db = database.get_db()
            db.execute('UPDATE users SET stats_public = 1 WHERE username = ?', ('alice',))
            db.close()


if __name__ == '__main__':
    unittest.main()
