# server.py
import base64
import tempfile

import litserve as ls
import torch

from mini_omni.inference import OmniInference

torch.set_float32_matmul_precision("medium")


class MiniOmni(ls.LitAPI):
    def setup(self, device):
        self.client = OmniInference(ckpt_dir="./checkpoint", device=device)
        self.client.warm_up()

    def decode_request(self, request):
        # Convert the request payload to model input.
        data_buf = request["audio"].encode("utf-8")
        data_buf = base64.b64decode(data_buf)
        stream_stride = request.get("stream_stride", 4)
        max_tokens = request.get("max_tokens", 2048)
        print(f"stream_stride: {stream_stride}, max_tokens: {max_tokens}")
        return data_buf, stream_stride, max_tokens

    def predict(self, inputs):
        # Run inference and return the output.
        data_buf, stream_stride, max_tokens = inputs
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(data_buf)
            audio_file = f.name

            audio_generator = self.client.run_AT_batch_stream(
                audio_file, stream_stride, max_tokens
            )
        yield from audio_generator

    def encode_response(self, output):
        yield from output


# (STEP 2) - START THE SERVER
if __name__ == "__main__":
    api = MiniOmni()
    server = ls.LitServer(api, accelerator="auto", api_path="/chat", stream=True)
    server.run(port=8000)
