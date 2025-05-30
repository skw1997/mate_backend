from multiprocessing import Process, freeze_support
from web.testpage import app
import uvicorn


def main() -> None:
    """Entrypoint of the application."""
    uvicorn.run("web.testpage:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    freeze_support() 
    main()
