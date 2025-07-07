import io
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional
import numpy as np
from PIL import Image
from .base import BaseComdec


class MJPEGHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        user_agent = self.headers.get('User-Agent', '').lower()
        is_vlc = 'vlc' in user_agent
        # Default: browser-compatible (no trailing CRLF after image, no CRLF before boundary)
        # VLC: add CRLF before boundary after first frame and after image
        self.send_response(200)
        self.send_header(
            'Content-type', 'multipart/x-mixed-replace; boundary=frame')
        self.end_headers()
        first = True
        try:
            while True:
                if hasattr(self.server, 'frame') and self.server.frame is not None:
                    img_bytes = self.server.frame
                    if is_vlc and not first:
                        self.wfile.write(b'\r\n')
                    if first:
                        first = False
                    self.wfile.write(b'--frame\r\n')
                    self.wfile.write(b'Content-Type: image/jpeg\r\n')
                    self.wfile.write(
                        f'Content-Length: {len(img_bytes)}\r\n'.encode())
                    self.wfile.write(b'\r\n')
                    self.wfile.write(img_bytes)
                    if is_vlc:
                        self.wfile.write(b'\r\n')
                    self.wfile.flush()
                import time
                time.sleep(1/30)  # 30 FPS
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            pass


class MJPEGServer(ThreadingHTTPServer):
    frame: Optional[bytes] = None

    def __init__(self, server_address):
        super().__init__(server_address, MJPEGHandler)
        self.frame = None


class MJPEGComdec(BaseComdec):
    """Comdec that streams numpy array frames as MJPEG over HTTP."""

    def __init__(self, port=8080, **config):
        super().__init__("mjpeg", **config)
        self.server = MJPEGServer(('0.0.0.0', port))
        self.thread = threading.Thread(
            target=self.server.serve_forever, daemon=True)
        self.thread.start()

    async def consume(self, frame, metadata=None):
        if isinstance(frame, np.ndarray):
            img = Image.fromarray(frame)
            buf = io.BytesIO()
            img.save(buf, format='JPEG')
            self.server.frame = buf.getvalue()
        return True
