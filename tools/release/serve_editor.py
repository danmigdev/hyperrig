"""Serve HyperRig locally. Requires Python 3.12+ and Edge or Chrome for USB."""
from functools import partial
import http.server
from pathlib import Path
import threading
import webbrowser


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_POST(self):
        # The local diagnostic endpoint discards data; nothing is uploaded.
        size = int(self.headers.get("Content-Length", "0"))
        if self.path != "/log" or not 0 <= size <= 1024 * 1024:
            self.send_error(400)
            return
        self.rfile.read(size)
        self.send_response(204)
        self.end_headers()


if __name__ == "__main__":
    folder = Path(__file__).resolve().parent / "web"
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(folder)))
    url = f"http://127.0.0.1:{server.server_port}/tankmini.html"
    print(f"HyperRig MINI editor: {url}\nKeep this window open. Press Ctrl+C to stop.")
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
