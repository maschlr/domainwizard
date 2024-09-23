from openai import OpenAI

from ..config import config

client = OpenAI(api_key=config["OPENAI_API_KEY"])


def get_embeddings(text, model="text-embedding-3-small"):
    response = client.embeddings.create(input=text, model=model)
    return response.data[0].embedding
