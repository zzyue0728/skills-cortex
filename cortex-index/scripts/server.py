import http.server
import json
import os
import sys
import threading
import time

WORK_DIR = sys.argv[1] if len(sys.argv) > 1 else '.'

# 运行时元数据文件
PID_FILE = os.path.join(WORK_DIR, 'server.pid')
PORT_FILE = os.path.join(WORK_DIR, 'server.port')

def cleanup_files():
    """删除 PID 和端口文件"""
    for f in (PID_FILE, PORT_FILE):
        try:
            os.remove(f)
        except OSError:
            pass

def do_shutdown(httpd):
    """延迟关闭服务器并清理"""
    def _shutdown():
        time.sleep(1)
        httpd.shutdown()
    threading.Thread(target=_shutdown, daemon=True).start()

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = os.path.join(WORK_DIR, 'review.html')
        if not os.path.exists(path):
            self.send_error(404, 'review.html not found')
            return
        with open(path, 'rb') as f:
            content = f.read()
        if b'__REVIEW_DATA__' in content:
            data_path = os.path.join(WORK_DIR, 'review_data.json')
            if os.path.exists(data_path):
                with open(data_path, 'rb') as df:
                    content = content.replace(b'__REVIEW_DATA__', df.read())
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        if self.path == '/save':
            self._handle_save()
        elif self.path == '/shutdown':
            self._handle_shutdown()
        else:
            self.send_error(404)

    def _handle_save(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length))
            save_path = os.path.join(WORK_DIR, 'save_result.json')
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode())
            # 保存成功后延迟关闭，给浏览器足够时间接收响应
            do_shutdown(httpd)
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode())

    def _handle_shutdown(self):
        """优雅关闭端点 — 用于用户取消审查时手动停止服务器"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'shutting_down'}).encode())
        do_shutdown(httpd)

    def log_message(self, format, *args):
        pass  # 静默 HTTP 日志

# 查找可用端口，从默认 18888 开始
PORT = 18888
while True:
    try:
        httpd = http.server.HTTPServer(('127.0.0.1', PORT), Handler)
        break
    except OSError:
        PORT += 1

# 写入 PID 和端口文件
with open(PID_FILE, 'w') as f:
    f.write(str(os.getpid()))
with open(PORT_FILE, 'w') as f:
    f.write(str(PORT))

print(f'http://127.0.0.1:{PORT}')

try:
    httpd.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    httpd.server_close()
    cleanup_files()
