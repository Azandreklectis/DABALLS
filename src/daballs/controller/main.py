
from fastapi import FastAPI

app = FastAPI(
    title="DABALLS Controller",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Report whether the DABALLS controller is responding."""
    return {
        "status": "ok",
        "service": "daballs-controller",
        "version": "0.1.0",
    }
