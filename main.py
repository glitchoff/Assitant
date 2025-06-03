from fastapi import FastAPI
from fastapi.responses import FileResponse, Form

app = FastAPI()

@app.get("/")
def render_static():
    return FileResponse("static/index.html")

@app.post("/upload")
def handle_form(file: str = Form(...)):
    return {"file": file}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
