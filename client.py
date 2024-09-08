import base64
import sys
import threading
import time
import traceback

import numpy as np
import pyaudio
import requests
import librosa
from mini_omni.utils.vad import get_speech_timestamps, collect_chunks, VadOptions

API_URL = "https://8000-01j78y8pf1nes8jqpy1w44qsgw.cloudspaces.litng.ai/chat"

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

CURSOR_CHARS = ["|", "/", "-", "\\"]


def run_vad(ori_audio, sr):
    _st = time.time()
    try:
        audio = np.frombuffer(ori_audio, dtype=np.int16)
        audio = audio.astype(np.float32) / 32768.0
        sampling_rate = 16000
        if sr != sampling_rate:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=sampling_rate)

        vad_parameters = {}
        vad_parameters = VadOptions(**vad_parameters)
        speech_chunks = get_speech_timestamps(audio, vad_parameters)
        audio = collect_chunks(audio, speech_chunks)
        duration_after_vad = audio.shape[0] / sampling_rate

        if sr != sampling_rate:
            vad_audio = librosa.resample(audio, orig_sr=sampling_rate, target_sr=sr)
        else:
            vad_audio = audio
        vad_audio = np.round(vad_audio * 32768.0).astype(np.int16)
        vad_audio_bytes = vad_audio.tobytes()

        return duration_after_vad, vad_audio_bytes, round(time.time() - _st, 4)
    except Exception as e:
        msg = f"[asr vad error] audio_len: {len(ori_audio)/(sr*2):.3f} s, trace: {traceback.format_exc()}"
        print(msg)
        return -1, ori_audio, round(time.time() - _st, 4)


def play_audio(response):
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=OUT_FORMAT, channels=OUT_CHANNELS, rate=OUT_RATE, output=True
    )
    try:
        for chunk in response.iter_content(chunk_size=OUT_CHUNK):
            if chunk:
                audio_data = np.frombuffer(chunk, dtype=np.int16)
                stream.write(audio_data.tobytes())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()


def send_audio(audio_data):
    encoded_audio = base64.b64encode(audio_data).decode("utf-8")
    response = requests.post(API_URL, json={"audio": encoded_audio}, stream=True)
    if response.status_code == 200:
        play_audio(response)
    else:
        print(f"Request failed with status code {response.status_code}")


def record_and_send():
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=IN_FORMAT,
        channels=IN_CHANNELS,
        rate=IN_RATE,
        input=True,
        frames_per_buffer=IN_CHUNK,
    )
    print("Recording... Press Ctrl+C to stop.")
    temp_audio = b""
    start_talking = False
    last_temp_audio = None

    try:
        while True:
            audio_data = stream.read(IN_CHUNK)
            temp_audio += audio_data

            if len(temp_audio) > IN_SAMPLE_WIDTH * IN_RATE * IN_CHANNELS * VAD_STRIDE:
                dur_vad, vad_audio_bytes, time_vad = run_vad(temp_audio, IN_RATE)
                print(
                    f"duration_after_vad: {dur_vad:.3f} s, time_vad: {time_vad:.3f} s"
                )

                if dur_vad > 0.2 and not start_talking:
                    if last_temp_audio is not None:
                        send_audio(last_temp_audio)
                    start_talking = True
                if start_talking:
                    send_audio(temp_audio)
                if dur_vad < 0.1 and start_talking:
                    print("Detected a long pause, stopping...")
                    break
                last_temp_audio = temp_audio
                temp_audio = b""
            time.sleep(0.1)
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
