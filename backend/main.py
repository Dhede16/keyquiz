"""Root launcher for KeyQuiz FastAPI server."""
import uvicorn
from app.main import app
from app.config import HOST, PORT

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
