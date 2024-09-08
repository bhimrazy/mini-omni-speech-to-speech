# server.py
import base64
import tempfile

import litserve as ls

from mini_omni.inference import OmniInference


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

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(data_buf)
            return f.name, stream_stride, max_tokens

    def predict(self, x):
        # Easily build compound systems. Run inference and return the output.
        squared = self.model1(x)
        cubed = self.model2(x)
        output = squared + cubed
        return {"output": output}

    def encode_response(self, output):
        # Convert the model output to a response payload.
        return {"output": output}


# (STEP 2) - START THE SERVER
if __name__ == "__main__":
    server = ls.LitServer(MiniOmni(), accelerator="auto", api_path="/chat")
    server.run(port=8000)
