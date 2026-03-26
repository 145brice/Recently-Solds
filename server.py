"""
Local Pipeline Server - http://localhost:8082
Serves the front-end dashboard + admin panel and the pipeline API.
"""

import http.server
import json
import threading
import subprocess
import sys
import os
from datetime import datetime
from urllib.parse import unquote

PORT = 8082
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, '..', 'Property-Managers--Front-End')
RUNNER = os.path.join(PROJECT_ROOT, 'run_daily.py')

MIME_TYPES = {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.csv': 'text/csv',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.ico': 'image/x-icon',
}

pipeline_status = {
    'running': False,
    'last_run': None,
    'last_result': None,
    'log': ''
}


def run_pipeline_thread(config):
    pipeline_status['running'] = True
    pipeline_status['log'] = ''
    pipeline_status['last_result'] = None

    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['ENABLED_COUNTIES'] = config.get('enabled_counties', 'all')
    env['DAVIDSON_DAYS'] = str(config.get('davidson_days', 60))
    env['WILSON_SUMNER_DAYS'] = str(config.get('wilson_sumner_days', 7))
    env['WILLIAMSON_DAYS'] = str(config.get('williamson_days', 30))
    env['MIN_PRICE'] = str(config.get('min_price', 150000))
    env['MAX_PRICE'] = str(config.get('max_price', 1500000))

    try:
        process = subprocess.Popen(
            [sys.executable, '-u', RUNNER],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=PROJECT_ROOT,
            env=env,
            bufsize=1
        )

        for line in process.stdout:
            pipeline_status['log'] += line

        process.wait()

        if process.returncode == 0:
            pipeline_status['last_result'] = 'success'
            pipeline_status['log'] += '\n--- Pipeline finished successfully ---\n'
        else:
            pipeline_status['last_result'] = 'error'
            pipeline_status['log'] += f'\n--- Pipeline exited with code {process.returncode} ---\n'

    except Exception as e:
        pipeline_status['last_result'] = 'error'
        pipeline_status['log'] += f'\n--- Error: {e} ---\n'

    pipeline_status['running'] = False
    pipeline_status['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


class Handler(http.server.BaseHTTPRequestHandler):

    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        path = unquote(self.path.split('?')[0])

        # API: pipeline status
        if path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(pipeline_status).encode())
            return

        # Serve front-end files
        if path == '/':
            path = '/index.html'

        file_path = os.path.normpath(os.path.join(FRONTEND_DIR, path.lstrip('/')))

        # Security: don't serve outside FRONTEND_DIR
        if not file_path.startswith(os.path.normpath(FRONTEND_DIR)):
            self.send_response(403)
            self.end_headers()
            return

        if os.path.isfile(file_path):
            ext = os.path.splitext(file_path)[1].lower()
            content_type = MIME_TYPES.get(ext, 'application/octet-stream')

            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self._cors_headers()
            self.end_headers()

            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>404 Not Found</h1>')

    def do_POST(self):
        if self.path == '/api/run':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()

            if pipeline_status['running']:
                self.wfile.write(json.dumps({'error': 'Pipeline already running'}).encode())
            else:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length) if content_length else b'{}'
                try:
                    config = json.loads(body)
                except json.JSONDecodeError:
                    config = {}

                thread = threading.Thread(target=run_pipeline_thread, args=(config,), daemon=True)
                thread.start()
                self.wfile.write(json.dumps({'status': 'started'}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    server = http.server.HTTPServer(('localhost', PORT), Handler)
    print(f"Server running at http://localhost:{PORT}")
    print(f"  Dashboard:  http://localhost:{PORT}/")
    print(f"  Admin:      http://localhost:{PORT}/admin.html")
    print(f"  Serving:    {FRONTEND_DIR}")
    print("Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()
