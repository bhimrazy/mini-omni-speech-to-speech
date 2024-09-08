import base64
import io
import wave

import numpy as np
import pyaudio
import requests

from cursor import RotatingCursor

IN_FORMAT = pyaudio.paInt16
IN_CHANNELS = 1
IN_RATE = 24000
IN_CHUNK = 1024
IN_SAMPLE_WIDTH = 2
VAD_STRIDE = 0.5

OUT_FORMAT = pyaudio.paInt16
OUT_CHANNELS = 1
OUT_RATE = 24000
OUT_CHUNK = 5760

# API URL
API_URL = "https://8000-01j78y8pf1nes8jqpy1w44qsgw.cloudspaces.litng.ai/chat"


def record_audio():
    p = pyaudio.PyAudio()
    stream = p.open(
        format=IN_FORMAT,
        channels=IN_CHANNELS,
        rate=IN_RATE,
        input=True,
        frames_per_buffer=IN_CHUNK,
    )

    frames = []

    try:
        while True:
            audio_bytes = stream.read(IN_CHUNK)
            frames.append(audio_bytes)

    except KeyboardInterrupt:
        print("\n* Recording stopped by KeyboardInterrupt")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

    buffer = b"".join(frames)

    wav_data = None

    with io.BytesIO() as f:
        with wave.open(f, "wb") as wf:
            wf.setnchannels(IN_CHANNELS)
            wf.setsampwidth(IN_SAMPLE_WIDTH)
            wf.setframerate(IN_RATE)
            wf.writeframes(buffer)
            wav_data = f.getvalue()

    return wav_data


def send_audio_to_api(audio_data):
    encoded_audio = base64.b64encode(audio_data).decode("utf-8")
    response = requests.post(API_URL, json={"audio": encoded_audio}, stream=True)
    return response


def play_audio_response(response):
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=OUT_FORMAT, channels=OUT_CHANNELS, rate=OUT_RATE, output=True
    )

    try:
        for chunk in response.iter_content(chunk_size=OUT_CHUNK):
            if chunk:
                audio_data = np.frombuffer(chunk, dtype=np.int16)
                stream.write(audio_data.tobytes())
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()


def main():
    while True:
        with RotatingCursor(text="Listening", cursor_chars=".oOo.", interval=0.1):
            audio_data = record_audio()

        with RotatingCursor(text="Processing"):
            response = send_audio_to_api(audio_data)

        with RotatingCursor(text="Speaking"):
            play_audio_response(response)


if __name__ == "__main__":
    main()
