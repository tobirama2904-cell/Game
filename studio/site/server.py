#!/usr/bin/env python3
"""Tiny static server with HTTP Range support (video seeking) for the studio site."""
import os
import re
import socketserver
from http.server import SimpleHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # studio/


META = {
    'trailer_noks': ('ХРОНИКИ ИСКРЫ', 'Книга первая: НОКС. Игры Тени', 'Дистопия • трейлер книги', '#7fd4e8'),
    'trailer_bone': ('КОСТЯНОЙ ПРИЛИВ', 'Тёмное фэнтези о тех, кто слышит чужой страх', 'Тёмное фэнтези • трейлер книги', '#c9b98a'),
    'trailer_strannik': ('СТРАННИК', 'Он видит город насквозь. Город видит его.', 'Городской триллер • трейлер книги', '#9fb4d8'),
    'trailer_razlom': ('РАЗЛОМ', 'Реальность дала трещину', 'Научная фантастика • трейлер книги', '#e08a8a'),
    'teaser': ('ЧЕТЫРЕ ИСТОРИИ', 'Одна трещина. Общий тизер четырёх книг', 'Тизер цикла', '#d8d8e8'),
}


def build_manifest():
    import json
    out = os.path.join(ROOT, 'out')
    tr = []
    td = os.path.join(out, 'trailers')
    if os.path.isdir(td):
        for f in sorted(os.listdir(td)):
            if f.endswith('.mp4') and os.path.getsize(os.path.join(td, f)) > 100_000:
                key = f[:-4]
                t, s, g, c = META.get(key, (key, '', '', '#cccccc'))
                item = {'id': key, 'title': t, 'sub': s, 'genre': g, 'color': c,
                        'file': f'/out/trailers/{f}',
                        'size': round(os.path.getsize(os.path.join(td, f)) / 1e6, 1)}
                if os.path.exists(os.path.join(td, key + '.jpg')):
                    item['poster'] = f'/out/trailers/{key}.jpg'
                if os.path.exists(os.path.join(td, key + '.srt')):
                    item['srt'] = f'/out/trailers/{key}.srt'
                tr.append(item)
    ab = []
    ad = os.path.join(out, 'audiobook')
    if os.path.isdir(ad):
        for book in sorted(os.listdir(ad)):
            bd = os.path.join(ad, book)
            if not os.path.isdir(bd):
                continue
            chapters = []
            for f in sorted(os.listdir(bd)):
                if f.endswith('.mp3'):
                    chapters.append({'file': f'/out/audiobook/{book}/{f}',
                                     'title': f[:-4].replace('_', ' '),
                                     'size': round(os.path.getsize(os.path.join(bd, f)) / 1e6, 1)})
            if chapters:
                ab.append({'id': book, 'chapters': chapters})
    return json.dumps({'trailers': tr, 'audiobook': ab}, ensure_ascii=False)


class RangeHandler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self.send_response(302)
            self.send_header('Location', '/site/')
            self.end_headers()
            return
        if self.path == '/site/' or self.path == '/site':
            self.path = '/site/index.html'
        if self.path.split('?')[0].endswith('/manifest.json'):
            data = build_manifest().encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(data)
            return
        return super().do_GET()

    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            path = os.path.join(path, 'index.html')
        rng = self.headers.get('Range')
        if not rng or not os.path.isfile(path):
            return super().send_head()
        size = os.path.getsize(path)
        m = re.match(r'bytes=(\d*)-(\d*)', rng)
        a, b = m.groups()
        a = int(a) if a else 0
        b = int(b) if b else size - 1
        b = min(b, size - 1)
        f = open(path, 'rb')
        f.seek(a)
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Content-Range', f'bytes {a}-{b}/{size}')
        self.send_header('Content-Length', str(b - a + 1))
        self.send_header('Accept-Ranges', 'bytes')
        self.end_headers()
        self._limit = b - a + 1
        return _Limited(f, self._limit)

    def log_message(self, *a):
        pass


class _Limited:
    def __init__(self, f, limit):
        self.f, self.left = f, limit

    def read(self, n=-1):
        if self.left <= 0:
            return b''
        n = n if n > 0 else self.left
        data = self.f.read(min(n, self.left))
        self.left -= len(data)
        return data

    def close(self):
        self.f.close()


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8000'))
    with Server(('0.0.0.0', port), RangeHandler) as httpd:
        print(f'serving on :{port}')
        httpd.serve_forever()
