import pyaudio
import requests
import base64
import threading
import time
import sys

# Server URL
SERVER_URL = "http://localhost:8000/chat"

# Audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024

# Rotating cursor characters
CURSOR_CHARS = ["|", "/", "-", "\\"]


def send_audio_data(audio_data):
    encoded_audio = base64.b64encode(audio_data).decode("utf-8")
    payload = {"audio": encoded_audio, "stream_stride": 4, "max_tokens": 2048}
    response = requests.post(SERVER_URL, json=payload)
    if response.status_code == 200:
        print("\nReceived response from server")
        # Handle the response (e.g., play the audio, print text, etc.)
    else:
        print(f"\nRequest failed with status code {response.status_code}")
        print(response.text)


def record_and_send():
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK
    )

    print("Recording and sending audio data...")

    try:
        while True:
            audio_data = stream.read(CHUNK)
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
