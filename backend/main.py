from domainwizard.config import config
from domainwizard.routes import app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=config.get("FASTAPI_PORT", 8000))
