import base64
import sys
import threading
import time

import numpy as np
import pyaudio
import requests

# Server URL
API_URL = "https://8000-01j78y8pf1nes8jqpy1w44qsgw.cloudspaces.litng.ai/chat"

# recording parameters
IN_FORMAT = pyaudio.paInt16
IN_CHANNELS = 1
IN_RATE = 24000
IN_CHUNK = 1024
IN_SAMPLE_WIDTH = 2
VAD_STRIDE = 0.5

# playing parameters
OUT_FORMAT = pyaudio.paInt16
OUT_CHANNELS = 1
OUT_RATE = 24000
OUT_SAMPLE_WIDTH = 2
OUT_CHUNK = 5760

# Rotating cursor characters
CURSOR_CHARS = ["|", "/", "-", "\\"]


def play_audio_from_response(response):
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=OUT_FORMAT,
        channels=OUT_CHANNELS,
        rate=OUT_RATE,
        output=True,
    )

    try:
        output_audio_bytes = b""
        for chunk in response.iter_content(chunk_size=OUT_CHUNK):
            if chunk:
                output_audio_bytes += chunk
                audio_data = np.frombuffer(chunk, dtype=np.int16)
                stream.write(audio_data.tobytes())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()


def send_audio_data(audio_data):
    encoded_audio = base64.b64encode(audio_data).decode("utf-8")
    files = {"audio": encoded_audio}

    with requests.post(API_URL, json=files, stream=True) as response:
        if response.status_code == 200:
            play_audio_from_response(response)
        else:
            print(f"Request failed with status code {response.status_code}")
            print(response.text)


def record_and_send():
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=IN_FORMAT,
        channels=IN_CHANNELS,
        rate=IN_RATE,
        input=True,
        frames_per_buffer=IN_CHUNK,
    )

    print("Recording and sending audio data...")

    try:
        while True:
            audio_data = stream.read(IN_CHUNK)
            # threading.Thread(target=send_audio_data, args=(audio_data,)).start()
            time.sleep(0.1)  # Adjust the sleep time as needed
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()


def rotating_cursor():
    while True:
        for char in CURSOR_CHARS:
            sys.stdout.write(f"\rListening {char}")
            sys.stdout.flush()
            time.sleep(0.1)


if __name__ == "__main__":
    cursor_thread = threading.Thread(target=rotating_cursor)
    cursor_thread.daemon = True
    cursor_thread.start()
    record_and_send()
