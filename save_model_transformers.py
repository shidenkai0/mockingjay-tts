import bentoml
from bark_vocos import BarkVocos
from processing_bark import BarkProcessor

model_id = "suno/bark"

processor = BarkProcessor.from_pretrained(model_id)
model = BarkVocos.from_pretrained(model_id)

bentoml.transformers.save_model('bark_processor', processor)


def get_framework(self):
    return "torch"


model.__class__.framework = property(get_framework)  # Necessary for BentoML to recognize the framework of the model
print(f"model.framework: {model.framework}")

bentoml.transformers.save_model(
    'bark_vocos_model', model, signatures={"generate": {"batchable": False}}, metadata={"_framework": "torch"}
)
