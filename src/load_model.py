import torch
from bark.bark_vocos import BarkVocos


model_id = "suno/bark"
model_path = "./bark-model"
model = BarkVocos.from_pretrained(model_id, torch_dtype=torch.float32)
