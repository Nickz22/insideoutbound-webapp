from dotenv import load_dotenv

load_dotenv()
from openai import OpenAI


def list_models():
    """
    Lists all available models from the OpenAI client.

    Returns:
        list: A list of all available models.
    """
    open_ai = OpenAIClient()
    return open_ai.get_models()


def invoke_chained_commands_without_assistant(commands, model):
    try:
        client = OpenAIClient().client
        models = client.models.list()

        completion = client.chat.completions.create(
            model=model,
            messages=commands,
        )
        return {"data": completion.choices[0].message.content}
    except Exception as e:
        return {"data": "error"}


class OpenAIClient:
    def __init__(self):
        """
        Constructor for the OpenAIClient class. Initializes an OpenAI client.
        """
        self.client = OpenAI()

    def get_models(self):
        """
        Returns a list of all available models from the OpenAI client.
        """
        return self.client.models.list()
