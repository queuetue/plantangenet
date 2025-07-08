"""
WebSocket Bidirectional Comdec - Real-time bidirectional streaming
Based on the MJPEG comdec pattern but extended for WebSocket communication.
"""
import asyncio
import json
import threading
import time
import uuid
from typing import Any, Dict, Optional, Callable, Set, Protocol
import numpy as np
from websockets import serve, WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed, WebSocketException
from .base import BaseComdec


class WebSocketStream:
    """Represents a single WebSocket connection/stream."""

    def __init__(self, websocket: WebSocketServerProtocol, stream_id: str, metadata: Optional[Dict[str, Any]] = None):
        self.websocket = websocket
        self.stream_id = stream_id
        self.metadata = metadata or {}
        # Topics this stream subscribes to
        self.subscriptions: Set[str] = set()
        self.last_ping = time.time()

    async def send_message(self, message_type: str, data: Any, metadata: Optional[Dict[str, Any]] = None):
        """Send a structured message to this stream."""
        try:
            message = {
                "type": message_type,
                "data": data,
                "metadata": metadata or {},
                "timestamp": time.time(),
                "stream_id": self.stream_id
            }
            await self.websocket.send(json.dumps(message))
            return True
        except (ConnectionClosed, WebSocketException) as e:
            print(f"WebSocket send failed for stream {self.stream_id}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error sending to stream {self.stream_id}: {e}")
            return False

    async def ping(self):
        """Send a ping to keep connection alive."""
        try:
            await self.websocket.ping()
            self.last_ping = time.time()
            return True
        except Exception:
            return False


class FrameProducer(Protocol):
    def __call__(self, state: Any) -> np.ndarray:
        ...


class WebSocketBidirectionalComdec(BaseComdec):
    """
    Bidirectional WebSocket comdec for real-time streaming.

    Combines:
    - Outbound: compositor frames/data → WebSocket clients (like MJPEG)
    - Inbound: WebSocket messages → callback handlers (backchannel)

    Message format (NATS-style envelope):
    {
        "type": "message_type",
        "data": {...},
        "metadata": {...},
        "timestamp": 1234567890.123,
        "stream_id": "client_uuid"
    }

    Supports pluggable frame producers:
    - Pass a frame_producer callable or object with __call__(state) -> np.ndarray
    - Example:
        def my_drawer(state):
            ... # return np.ndarray
        comdec = WebSocketBidirectionalComdec(frame_producer=my_drawer)
    """

    def __init__(self, port: int = 8765, host: str = "0.0.0.0",
                 message_handler: Optional[Callable] = None,
                 broadcast_fps: int = 30,
                 frame_producer: Optional[FrameProducer] = None,
                 **config):
        super().__init__("websocket_bidirectional", **config)
        self.host = host
        self.port = port
        self.streams: Dict[str, WebSocketStream] = {}
        self.message_handler = message_handler
        self.server = None
        self.server_task = None
        self.ping_task = None
        self.broadcast_task = None
        self.running = False
        self.broadcast_fps = broadcast_fps
        self.latest_frame = None
        self.latest_metadata = None
        self.latest_message_type = None
        self.frame_producer = frame_producer

    async def initialize(self) -> bool:
        """Start the WebSocket server."""
        try:
            self.running = True
            # Start WebSocket server
            self.server = await serve(
                self._handle_websocket,
                self.host,
                self.port,
                ping_interval=30,
                ping_timeout=10
            )
            print(f"WebSocket server started on ws://{self.host}:{self.port}")
            # Start ping task to keep connections alive
            self.ping_task = asyncio.create_task(self._ping_connections())
            # Start broadcast task for MJPEG-style streaming
            self.broadcast_task = asyncio.create_task(
                self._periodic_broadcast())
            return True
        except Exception as e:
            print(f"Failed to start WebSocket server: {e}")
            return False

    async def finalize(self) -> bool:
        """Stop the WebSocket server."""
        try:
            self.running = False
            # Cancel ping and broadcast tasks
            if self.ping_task:
                self.ping_task.cancel()
                try:
                    await self.ping_task
                except asyncio.CancelledError:
                    pass
            if self.broadcast_task:
                self.broadcast_task.cancel()
                try:
                    await self.broadcast_task
                except asyncio.CancelledError:
                    pass
            # Close all streams
            for stream in list(self.streams.values()):
                try:
                    await stream.websocket.close()
                except Exception:
                    pass
            self.streams.clear()

            # Stop server
            if self.server:
                self.server.close()
                await self.server.wait_closed()

            print("WebSocket server stopped")
            return True
        except Exception as e:
            print(f"Error stopping WebSocket server: {e}")
            return False

    async def _handle_websocket(self, websocket: WebSocketServerProtocol, path: str):
        """Handle a new WebSocket connection."""
        stream_id = str(uuid.uuid4())
        print(f"New WebSocket connection: {stream_id}")

        # Create stream object
        stream = WebSocketStream(websocket, stream_id)
        self.streams[stream_id] = stream

        try:
            # Send welcome message
            await stream.send_message("connected", {
                "stream_id": stream_id,
                "server": "plantangenet_websocket_comdec"
            })

            # Handle incoming messages
            async for message in websocket:
                await self._handle_incoming_message(stream, message)

        except ConnectionClosed:
            print(f"WebSocket connection closed: {stream_id}")
        except Exception as e:
            print(f"WebSocket error for {stream_id}: {e}")
        finally:
            # Clean up
            if stream_id in self.streams:
                del self.streams[stream_id]

    async def _handle_incoming_message(self, stream: WebSocketStream, raw_message: str):
        """Handle an incoming message from a WebSocket client."""
        try:
            # Parse message
            message = json.loads(raw_message)
            message_type = message.get("type", "unknown")
            data = message.get("data", {})
            metadata = message.get("metadata", {})

            # Update stream metadata
            stream.metadata.update(metadata.get("stream_metadata", {}))

            # Handle built-in message types
            if message_type == "subscribe":
                # Client wants to subscribe to specific topics/channels
                topics = data.get("topics", [])
                for topic in topics:
                    stream.subscriptions.add(topic)
                await stream.send_message("subscribed", {"topics": list(stream.subscriptions)})

            elif message_type == "unsubscribe":
                # Client wants to unsubscribe from topics
                topics = data.get("topics", [])
                for topic in topics:
                    stream.subscriptions.discard(topic)
                await stream.send_message("unsubscribed", {"topics": topics})

            elif message_type == "ping":
                # Client ping - respond with pong
                await stream.send_message("pong", {"timestamp": time.time()})

            else:
                # Forward to external message handler
                if self.message_handler:
                    try:
                        # Add stream context to message
                        enriched_message = {
                            **message,
                            "stream_id": stream.stream_id,
                            "stream_metadata": stream.metadata,
                            "subscriptions": list(stream.subscriptions)
                        }

                        # Call handler (can be async or sync)
                        if asyncio.iscoroutinefunction(self.message_handler):
                            await self.message_handler(enriched_message, stream)
                        else:
                            self.message_handler(enriched_message, stream)

                    except Exception as e:
                        print(f"Error in message handler: {e}")
                        await stream.send_message("error", {
                            "message": f"Handler error: {e}",
                            "original_type": message_type
                        })
                else:
                    # No handler - send back unhandled
                    await stream.send_message("unhandled", {
                        "original_type": message_type,
                        "message": "No message handler configured"
                    })

        except json.JSONDecodeError as e:
            await stream.send_message("error", {
                "message": f"Invalid JSON: {e}",
                "raw_message": raw_message
            })
        except Exception as e:
            await stream.send_message("error", {
                "message": f"Message processing error: {e}"
            })

    async def _ping_connections(self):
        """Periodically ping all connections to keep them alive."""
        while self.running:
            try:
                # Ping all streams
                dead_streams = []
                for stream_id, stream in self.streams.items():
                    if not await stream.ping():
                        dead_streams.append(stream_id)

                # Remove dead streams
                for stream_id in dead_streams:
                    if stream_id in self.streams:
                        del self.streams[stream_id]
                        print(f"Removed dead stream: {stream_id}")

                await asyncio.sleep(30)  # Ping every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Ping task error: {e}")
                await asyncio.sleep(5)

    async def _periodic_broadcast(self):
        """Periodically broadcast the latest frame to all clients (MJPEG style)."""
        interval = 1.0 / self.broadcast_fps if self.broadcast_fps > 0 else 1.0 / 30
        while self.running:
            try:
                if self.latest_frame is not None:
                    await self._broadcast_latest_frame()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Broadcast task error: {e}")
                await asyncio.sleep(1)

    async def _broadcast_latest_frame(self):
        """Send the latest frame to all connected/subscribed clients."""
        message_type = self.latest_message_type or "frame_generic"
        frame_data = self.latest_frame
        metadata = self.latest_metadata or {}
        dead_streams = []
        for stream_id, stream in self.streams.items():
            # Check if stream is subscribed to this type of data (if any subscriptions)
            if stream.subscriptions and message_type not in stream.subscriptions:
                continue
            try:
                await stream.send_message(message_type, frame_data, metadata)
            except Exception:
                dead_streams.append(stream_id)
        for stream_id in dead_streams:
            if stream_id in self.streams:
                del self.streams[stream_id]

    async def consume(self, frame: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store the latest frame and metadata for periodic broadcast (MJPEG style).
        If a frame_producer is set, use it to generate the frame from state.
        Return True if there are active clients, else False (for test compatibility).
        """
        try:
            has_clients = bool(self.streams)
            # If a frame producer is set, use it
            if self.frame_producer is not None:
                frame = self.frame_producer(frame)
            # Determine message type and serialize frame
            if isinstance(frame, np.ndarray):
                message_type = "frame_array"
                frame_data = {
                    "shape": frame.shape,
                    "dtype": str(frame.dtype),
                    "data": frame.tolist()
                }
            elif isinstance(frame, dict):
                message_type = "frame_data"
                frame_data = frame
            else:
                message_type = "frame_generic"
                frame_data = {"value": str(
                    frame), "type": type(frame).__name__}
            # Store for broadcast
            self.latest_frame = frame_data
            self.latest_metadata = metadata or {}
            self.latest_message_type = message_type
            # Always increment stats (for test compatibility)
            self.frame_count += 1
            self.stats['frames_consumed'] += 1
            self.stats['last_frame_time'] = time.time()
            self.stats['bytes_processed'] += len(json.dumps(frame_data))
            return has_clients
        except Exception as e:
            self.stats['errors'] += 1
            print(f"WebSocketBidirectionalComdec error: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics including connection info."""
        base_stats = super().get_stats()
        base_stats.update({
            'active_streams': len(self.streams),
            'stream_ids': list(self.streams.keys()),
            'subscriptions': {
                stream_id: list(stream.subscriptions)
                for stream_id, stream in self.streams.items()
            },
            'server_running': self.running,
            'host': self.host,
            'port': self.port
        })
        return base_stats

    async def broadcast_to_topic(self, topic: str, message_type: str, data: Any, metadata: Optional[Dict[str, Any]] = None):
        """Broadcast a message to all streams subscribed to a specific topic."""
        successful_sends = 0
        for stream in self.streams.values():
            if topic in stream.subscriptions:
                success = await stream.send_message(message_type, data, metadata)
                if success:
                    successful_sends += 1
        return successful_sends

    def get_stream_by_id(self, stream_id: str) -> Optional[WebSocketStream]:
        """Get a specific stream by ID."""
        return self.streams.get(stream_id)

# --- FrameProducer Adapters ---


def pil_drawer_adapter(draw_func):
    """
    Adapter for PIL-based draw functions.
    draw_func(state) -> PIL.Image.Image
    Returns a FrameProducer that outputs np.ndarray (RGB).
    """
    from PIL import Image

    def wrapper(state):
        img = draw_func(state)
        if not isinstance(img, Image.Image):
            raise ValueError("PIL drawer must return a PIL.Image.Image")
        return np.array(img.convert("RGB"))
    return wrapper


def opencv_drawer_adapter(draw_func):
    """
    Adapter for OpenCV-based draw functions.
    draw_func(state) -> np.ndarray (BGR or RGB)
    Returns a FrameProducer that outputs np.ndarray (RGB).
    """
    import cv2

    def wrapper(state):
        frame = draw_func(state)
        if frame.ndim == 3 and frame.shape[2] == 3:
            # Assume BGR, convert to RGB
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame
    return wrapper

# Example usage:
# from PIL import Image, ImageDraw
# def my_pil_drawer(state):
#     img = Image.new("RGB", (100, 100), (255, 255, 255))
#     draw = ImageDraw.Draw(img)
#     draw.rectangle([10, 10, 90, 90], fill=(255, 0, 0))
#     return img
# comdec = WebSocketBidirectionalComdec(frame_producer=pil_drawer_adapter(my_pil_drawer))

# import cv2
# def my_cv_drawer(state):
#     frame = np.zeros((100, 100, 3), dtype=np.uint8)
#     cv2.rectangle(frame, (10, 10), (90, 90), (0, 0, 255), -1)
#     return frame
# comdec = WebSocketBidirectionalComdec(frame_producer=opencv_drawer_adapter(my_cv_drawer))
