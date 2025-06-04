from fastapi import FastAPI,File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
from utils.classifyfiles import processfile
app = FastAPI()

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.post("/classify")
def classify_file(file: UploadFile = File(...)):
    return processfile(file)
        


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
