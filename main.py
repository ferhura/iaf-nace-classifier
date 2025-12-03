import uvicorn
from iaf_nace_classifier.api import app

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
