import bentoml
import nltk
import numpy as np
import torch
import transformers
import io

from scipy.io.wavfile import write
from typing import Dict

processor_ref = bentoml.models.get("bark_processor:latest")


class BarkProcessorRunnable(bentoml.Runnable):
    SUPPORTED_RESOURCES = "cpu"
    SUPPORTS_CPU_MULTI_THREADING = False

    def __init__(self):
        self.processor = bentoml.transformers.load_model(processor_ref)
        nltk.download('punkt')

    @bentoml.Runnable.method(batchable=False)
    def process(self, input: str, voice_preset: str) -> Dict:
        input_sentences = nltk.tokenize.sent_tokenize(input)
        inputs = self.processor(input_sentences, voice_preset=voice_preset)
        print(f"inputs (in processor): {inputs}")
        return inputs


processor_runner = bentoml.Runner(BarkProcessorRunnable, name="bark_vocos_runner", models=[processor_ref])
tts_model_runner = bentoml.transformers.get("bark_vocos_model:latest").to_runner()

svc = bentoml.Service(name="bark_vocos", runners=[processor_runner, tts_model_runner])

input_spec = bentoml.io.JSON.from_sample({"text": "Hey", "voice_preset": "voice_presets/snoop-dogg-hb-7s.npz"})


@svc.api(input=input_spec, output=bentoml.io.File())
async def generate(input: Dict[str, str]) -> bytes:
    torch.manual_seed(48)
    inputs = await processor_runner.process.async_run(input["text"], input["voice_preset"])
    # move to GPU if available, this is a workaround for async_run
    if torch.cuda.is_available():
        for k, v in inputs.items():
            if isinstance(v, torch.Tensor):
                inputs[k] = v.cuda()
            elif isinstance(v, transformers.feature_extraction_utils.BatchFeature):
                for kk, vv in v.items():
                    if isinstance(vv, torch.Tensor):
                        inputs[k][kk] = vv.cuda()
    print(f"inputs: {inputs}")
    output = await tts_model_runner.generate.async_run(**inputs)

    # Assume output is a numpy array with a proper shape and dtype for audio data
    # And sample_rate is the audio sample rate
    sample_rate = 44100  # You should set this to the correct value for your model

    # Convert the numpy array to a WAV file in memory
    buffer = io.BytesIO()
    np_output = output.cpu().numpy().astype(np.float32)
    write(buffer, sample_rate, np_output)
    buffer.seek(0)  # Seek back to the start of the buffer

    return buffer.getvalue()
