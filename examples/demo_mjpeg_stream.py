import numpy as np
import time
from plantangenet.comdec.mjpeg import MJPEGComdec

# Demo: MJPEG streaming of a moving color bar


def main():
    width, height = 320, 240
    comdec = MJPEGComdec(port=8080)
    print("MJPEG stream running. Open VLC or a browser and go to: http://localhost:8080")
    print("Press Ctrl+C to stop.")
    t = 0
    try:
        while True:
            # Create a simple moving color bar
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            bar_pos = (t % width)
            frame[:, bar_pos:bar_pos+20, 0] = 255  # Red bar
            frame[:, (bar_pos+40) % width:(bar_pos+60) %
                  width, 1] = 255  # Green bar
            frame[:, (bar_pos+80) % width:(bar_pos+100) %
                  width, 2] = 255  # Blue bar
            # Send frame to comdec
            import asyncio
            asyncio.run(comdec.consume(frame))
            time.sleep(1/30)
            t += 4
    except KeyboardInterrupt:
        print("\nDemo stopped.")


if __name__ == "__main__":
    main()
