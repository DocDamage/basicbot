from bot.model.base_model import ModelSettings


class Phi3MiniSettings(ModelSettings):
    url = "microsoft/Phi-3-mini-4k-instruct"
    file_name = ""  # Not needed for HF models
    config = {}  # Not needed
    config_answer = {"temperature": 0.7, "stop": []}
