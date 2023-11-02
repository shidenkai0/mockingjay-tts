import torch
import torchaudio
from modeling_bark import BarkModel
from vocos import Vocos


class BarkVocos(BarkModel):
    @classmethod
    def from_pretrained(cls, pretrained_model_name_or_path, *model_args, **kwargs):
        model = super().from_pretrained(pretrained_model_name_or_path, *model_args, **kwargs)
        model.vocos = Vocos.from_pretrained("charactr/vocos-encodec-24khz")
        return model

    def codec_decode(self, fine_output: torch.Tensor):
        fine_output = fine_output.transpose(0, 1)
        features = self.vocos.codes_to_features(fine_output)
        audio = self.vocos.decode(features, bandwidth_id=torch.tensor([2], device=self.device))
        audio = torchaudio.functional.resample(
            audio, orig_freq=self.generation_config.sample_rate, new_freq=44100
        ).cpu()
        return audio
