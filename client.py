import base64
import io
import time
import wave

import numpy as np
import pyaudio
import requests

from cursor import RotatingCursor

# Audio recording configurations
AUDIO_INPUT_FORMAT = pyaudio.paInt16
AUDIO_INPUT_CHANNELS = 1
AUDIO_INPUT_RATE = 24000
AUDIO_INPUT_CHUNK = 1024
AUDIO_INPUT_SAMPLE_WIDTH = 2

MAX_RECORD_TIME = 15  # Maximum recording time in seconds
SILENCE_THRESHOLD = 500  # Adjust this value for silence detection
SILENCE_DURATION_LIMIT = 2  # Seconds of silence before stopping recording


# Audio playback configurations
AUDIO_OUTPUT_FORMAT = pyaudio.paInt16
AUDIO_OUTPUT_CHANNELS = 1
AUDIO_OUTPUT_RATE = 24000
AUDIO_OUTPUT_CHUNK = 5760

# API URL
API_URL = "https://8000-01j78y8pf1nes8jqpy1w44qsgw.cloudspaces.litng.ai/chat"


def is_silent(audio_data: bytes) -> bool:
    """Check if the audio data is below the silence threshold."""
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    return np.abs(audio_array).mean() < SILENCE_THRESHOLD


def record_audio() -> bytes:
    """Record audio with a maximum duration and stop if silence is detected."""
    pyaudio_instance = pyaudio.PyAudio()
    stream = pyaudio_instance.open(
        format=AUDIO_INPUT_FORMAT,
        channels=AUDIO_INPUT_CHANNELS,
        rate=AUDIO_INPUT_RATE,
        input=True,
        frames_per_buffer=AUDIO_INPUT_CHUNK,
    )

    audio_frames = []
    start_time = time.time()
    silence_start_time = None

    try:
        while True:
            audio_chunk = stream.read(AUDIO_INPUT_CHUNK)
            audio_frames.append(audio_chunk)

            # Check for silence
            if is_silent(audio_chunk):
                if silence_start_time is None:
                    silence_start_time = time.time()
                elif time.time() - silence_start_time >= SILENCE_DURATION_LIMIT:
                    break  # Exit if silence lasts longer than the limit
            else:
                silence_start_time = None  # Reset silence timer on activity

            # Stop recording after the max duration
            if time.time() - start_time >= MAX_RECORD_TIME:
                break

    except KeyboardInterrupt:
        pass
    finally:
        stream.stop_stream()
        stream.close()
        pyaudio_instance.terminate()

    # Combine all recorded frames into a WAV format in-memory file
    with io.BytesIO() as wav_buffer:
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(AUDIO_INPUT_CHANNELS)
            wav_file.setsampwidth(AUDIO_INPUT_SAMPLE_WIDTH)
            wav_file.setframerate(AUDIO_INPUT_RATE)
            wav_file.writeframes(b"".join(audio_frames))
        return wav_buffer.getvalue()


def send_audio_to_api(audio_data: bytes) -> requests.Response:
    """Send the audio data to the API and return the response."""
    encoded_audio = base64.b64encode(audio_data).decode("utf-8")
    response = requests.post(API_URL, json={"audio": encoded_audio}, stream=True)
    response.raise_for_status()
    return response


def play_audio_response(response: requests.Response):
    """Play the audio response from the API using the speaker."""
    pyaudio_instance = pyaudio.PyAudio()
    stream = pyaudio_instance.open(
        format=AUDIO_OUTPUT_FORMAT,
        channels=AUDIO_OUTPUT_CHANNELS,
        rate=AUDIO_OUTPUT_RATE,
        output=True,
    )

    try:
        for audio_chunk in response.iter_content(chunk_size=AUDIO_OUTPUT_CHUNK):
            if audio_chunk:
                audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
                stream.write(audio_data.tobytes())
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop_stream()
        stream.close()
        pyaudio_instance.terminate()


def main():
    """Main function to handle the audio recording, sending, and playback."""
    while True:
        with RotatingCursor(text="Listening", cursor_chars=".oOo.", interval=0.1):
            audio_data = record_audio()

        with RotatingCursor(text="Processing"):
            response = send_audio_to_api(audio_data)

        with RotatingCursor(text="Speaking"):
            play_audio_response(response)


if __name__ == "__main__":
    main()
