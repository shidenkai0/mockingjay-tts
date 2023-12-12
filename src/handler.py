import base64
import io
import numpy as np
import torch
import nltk
import runpod
from runpod.serverless.utils import rp_upload, rp_cleanup, rp_cuda

from bark.bark_vocos import BarkVocos
from bark.processing_bark import BarkProcessor
from runpod.serverless.utils.rp_validator import validate
from schemas import INPUT_SCHEMA
from scipy.io.wavfile import write as write_wav

device = "cuda:0" if rp_cuda.is_available() else "cpu"

# Load model and tokenizer

model_id = "suno/bark"
model_path = "./bark-model"
model = BarkVocos.from_pretrained(model_id, torch_dtype=torch.float32)

model = model.to(device)
model.to_bettertransformer()

processor = BarkProcessor.from_pretrained(model_id)

nltk.download("punkt")

semantic_temp = 0.7
coarse_temp = 0.7
fine_temp = 0.4
output_sample_rate = 44100
do_sample = True


def generate_audio(job):
    job_input = job["input"]

    print(f"Running job {job['id']} with input: {job_input}")

    # Validate input
    validated_input = validate(job_input, INPUT_SCHEMA)

    if 'errors' in validated_input:
        return {"error": validated_input['errors']}
    validated_input = validated_input['validated_input']

    text_prompt = validated_input["text_prompt"]

    # Load voice preset
    voice_preset_b64 = validated_input["voice_preset_base64"]
    voice_preset = dict(np.load(io.BytesIO(base64.b64decode(voice_preset_b64))))

    # Tokenize input
    sentences = nltk.sent_tokenize(text_prompt)
    inputs = processor(sentences, voice_preset=voice_preset)
    inputs.to(device)

    # Generate audio
    output = model.generate(
        **inputs,
        do_sample=do_sample,
        fine_temperature=fine_temp,
        coarse_temperature=coarse_temp,
        semantic_temperature=semantic_temp,
    )

    audio_filename = f"{job['id']}_audio.wav"

    output_path = f"/tmp/{audio_filename}"
    write_wav(output_path, output_sample_rate, output.cpu().numpy())

    # Upload output
    audio_url = rp_upload.upload_file_to_bucket(audio_filename, output_path)

    # Cleanup
    rp_cleanup.clean(["/tmp"])

    return {"audio_url": audio_url}


runpod.serverless.start({"handler": generate_audio})
