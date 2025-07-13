"""
Demo: WebSocketAudioMidiComdec - streams multichannel audio and MIDI events over WebSocket.
Run this, then connect a client to ws://localhost:9000 to receive audio and MIDI messages.
"""
import asyncio
import numpy as np
import time
from plantangenet.comdec.websocket import BaseComdec


class WebSocketAudioMidiComdec(BaseComdec):
    """
    Streams multichannel audio and MIDI events over WebSocket.
    - Audio frames: topic 'audio', PCM numpy arrays or bytes.
    - MIDI events: topic 'midi', dicts or bytes.
    """

    def __init__(self, port=9000, host="0.0.0.0", audio_fps=100, midi_fps=100, **config):
        super().__init__("websocket_audio_midi", **config)
        self.host = host
        self.port = port
        self.audio_fps = audio_fps
        self.midi_fps = midi_fps
        self.server = None
        self.clients = set()
        self.latest_audio = None
        self.latest_audio_meta = None
        self.latest_midi = None
        self.latest_midi_meta = None
        self.running = False

    async def initialize(self) -> bool:
        self.running = True
        import websockets
        self.server = await websockets.serve(self._handle_ws, self.host, self.port)
        asyncio.create_task(self._broadcast_audio())
        asyncio.create_task(self._broadcast_midi())
        print(f"Audio/MIDI WebSocket server on ws://{self.host}:{self.port}")
        return True

    async def finalize(self) -> bool:
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        return True

    async def consume(self, frame, metadata=None):
        # Dummy method to satisfy BaseComdec; not used in this demo.
        return True

    async def _handle_ws(self, ws, path):
        self.clients.add(ws)
        try:
            async for msg in ws:
                pass  # Optionally handle incoming MIDI or control messages here
        finally:
            self.clients.remove(ws)

    async def _broadcast_audio(self):
        interval = 1.0 / self.audio_fps
        while self.running:
            if self.latest_audio is not None:
                await self._send_to_all("audio", self.latest_audio, self.latest_audio_meta)
            await asyncio.sleep(interval)

    async def _broadcast_midi(self):
        interval = 1.0 / self.midi_fps
        while self.running:
            if self.latest_midi is not None:
                await self._send_to_all("midi", self.latest_midi, self.latest_midi_meta)
            await asyncio.sleep(interval)

    async def _send_to_all(self, topic, data, meta):
        import json
        msg = {
            "topic": topic,
            "data": data.tolist() if isinstance(data, np.ndarray) else data,
            "meta": meta or {},
            "timestamp": time.time()
        }
        for ws in list(self.clients):
            try:
                await ws.send(json.dumps(msg))
            except Exception:
                self.clients.discard(ws)

    async def consume_audio(self, frame: np.ndarray, meta=None):
        self.latest_audio = frame
        self.latest_audio_meta = meta or {}

    async def consume_midi(self, midi_event, meta=None):
        self.latest_midi = midi_event
        self.latest_midi_meta = meta or {}


async def main():
    comdec = WebSocketAudioMidiComdec()
    await comdec.initialize()

    # Demo: generate a sine wave and fake MIDI events
    t = 0
    midi_counter = 0
    try:
        while True:
            # Audio: 2ch, 512 samples, 44.1kHz, sine wave
            sr = 44100
            n = 512
            t_arr = np.arange(n) / sr + t
            audio = np.stack([
                0.1 * np.sin(2 * np.pi * 440 * t_arr),
                0.1 * np.sin(2 * np.pi * 660 * t_arr)
            ], axis=-1)  # shape (512, 2)
            await comdec.consume_audio(audio)
            t += n / sr
            # MIDI: send a fake note every second
            if int(t) > midi_counter:
                midi_event = {"type": "note_on", "note": 60 +
                              midi_counter % 12, "velocity": 100}
                await comdec.consume_midi(midi_event)
                midi_counter += 1
            await asyncio.sleep(0.005)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        await comdec.finalize()

if __name__ == "__main__":
    asyncio.run(main())
