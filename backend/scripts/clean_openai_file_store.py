import datetime as dt

import openai
from domainwizard.config import config
from loguru import logger

client = openai.Client(api_key=config["OPENAI_API_KEY"])

if __name__ == "__main__":
    now = dt.datetime.now(dt.UTC)
    file_response = client.files.list()
    for file in file_response:
        file_created_at = dt.datetime.fromtimestamp(file.created_at, dt.UTC)
        if (now - file_created_at).days > 7:
            logger.info(f"Deleting file {file.id} created at {file_created_at}")
            client.files.delete(file.id)
