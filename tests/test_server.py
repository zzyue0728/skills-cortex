"""Tests for memo-review/scripts/server.py."""
import contextlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

SERVER_SCRIPT = Path(__file__).parent.parent / 'memo-review' / 'scripts' / 'server.py'


@contextlib.contextmanager
def running_server(workdir):
    proc = subprocess.Popen(
        [sys.executable, str(SERVER_SCRIPT), str(workdir)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    port = None
    for _ in range(100):
        port_file = workdir / 'server.port'
        if port_file.exists():
            port = int(port_file.read_text(encoding='utf-8').strip())
            break
        time.sleep(0.05)
    if port is None:
        proc.terminate()
        proc.wait()
        raise RuntimeError('server.py 未在 5 秒内写出 server.port')
    try:
        yield port
    finally:
        try:
            urllib.request.urlopen(
                urllib.request.Request(f'http://127.0.0.1:{port}/shutdown', method='POST'),
                timeout=2,
            )
        except Exception:
            pass
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.terminate()
            proc.wait()


class ServerTestCase(unittest.TestCase):
    def setUp(self):
        self.workdir = Path(tempfile.mkdtemp(prefix='memo_test_'))

    def tearDown(self):
        shutil.rmtree(self.workdir, ignore_errors=True)

    def test_get_serves_html_with_data_injected(self):
        (self.workdir / 'review.html').write_text(
            '<html><body>__REVIEW_DATA__</body></html>', encoding='utf-8'
        )
        (self.workdir / 'review_data.json').write_text('{"x": 1}', encoding='utf-8')

        with running_server(self.workdir) as port:
            resp = urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=2)

        self.assertEqual(resp.status, 200)
        body = resp.read().decode('utf-8')
        self.assertNotIn('__REVIEW_DATA__', body)
        self.assertIn('"x": 1', body)

    def test_get_keeps_placeholder_when_data_missing(self):
        (self.workdir / 'review.html').write_text(
            '<html>__REVIEW_DATA__</html>', encoding='utf-8'
        )

        with running_server(self.workdir) as port:
            resp = urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=2)

        body = resp.read().decode('utf-8')
        self.assertIn('__REVIEW_DATA__', body)

    def test_get_404_when_review_html_missing(self):
        with running_server(self.workdir) as port:
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=2)

        self.assertEqual(ctx.exception.code, 404)

    def test_save_writes_file_and_stops_server(self):
        (self.workdir / 'review.html').write_text('<html></html>', encoding='utf-8')

        with running_server(self.workdir) as port:
            payload = json.dumps({'saved': True}).encode('utf-8')
            req = urllib.request.Request(
                f'http://127.0.0.1:{port}/save',
                data=payload,
                headers={'Content-Type': 'application/json'},
                method='POST',
            )
            resp = urllib.request.urlopen(req, timeout=2)
            self.assertEqual(resp.status, 200)

        save_path = self.workdir / 'save_result.json'
        self.assertTrue(save_path.exists())
        self.assertEqual(
            json.loads(save_path.read_text(encoding='utf-8')),
            {'saved': True},
        )

    def test_shutdown_endpoint_stops_server(self):
        (self.workdir / 'review.html').write_text('<html></html>', encoding='utf-8')

        with running_server(self.workdir) as port:
            resp = urllib.request.urlopen(
                urllib.request.Request(
                    f'http://127.0.0.1:{port}/shutdown', method='POST'
                ),
                timeout=2,
            )
            self.assertEqual(resp.status, 200)

        for _ in range(20):
            if not (self.workdir / 'server.pid').exists():
                break
            time.sleep(0.1)
        self.assertFalse(
            (self.workdir / 'server.pid').exists(),
            'server.py 优雅关闭后应清理 server.pid',
        )


if __name__ == '__main__':
    unittest.main()
