import os
import base64
import requests
import pyaudio
import numpy as np
import wave

# playing parameters
OUT_FORMAT = pyaudio.paInt16
OUT_CHANNELS = 1
OUT_RATE = 24000
OUT_SAMPLE_WIDTH = 2
OUT_CHUNK = 5760

API_URL = os.getenv("API_URL", "http://0.0.0.0:8000/chat")

# Read the audio file and encode it in base64
with open("mini_omni/data/samples/output2.wav", "rb") as audio_file:
    encoded_string = base64.b64encode(audio_file.read()).decode("utf-8")

# Define the request payload
files = {
    "audio": encoded_string,
}


# Send a POST request to the server
output_audio_bytes = b""
with requests.post(API_URL, json=files, stream=True) as response:
    try:
        for chunk in response.iter_content(chunk_size=OUT_CHUNK):
            if chunk:
                # Convert chunk to numpy array
                output_audio_bytes += chunk
                audio_data = np.frombuffer(chunk, dtype=np.int8)

                print(f"audio_data: {audio_data}")

    except Exception as e:
        print(f"Error: {e}")

# Open a wave file
with wave.open('output.wav', 'wb') as f:
    # Set the parameters: mono sound, 16 bit depth, 24000 sample rate
    f.setnchannels(OUT_CHANNELS)
    f.setsampwidth(OUT_SAMPLE_WIDTH)
    f.setframerate(OUT_RATE)
    # Write the audio data
    f.writeframes(output_audio_bytes)
