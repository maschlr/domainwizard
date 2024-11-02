import uvicorn
from domainwizard.config import config
from domainwizard.routes import app
from uvicorn.config import LOGGING_CONFIG

if __name__ == "__main__":
    LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s [%(name)s] %(levelprefix)s %(message)s"
    uvicorn.run(app, host="localhost", port=config.get("FASTAPI_PORT", 8000))
