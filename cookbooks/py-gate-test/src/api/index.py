from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"status": "ok", "note": "als je dit ziet zonder gate, lekt de API"}


@app.get("/api/hello")
def hello(name: str = "wereld"):
    return {"message": f"Hallo, {name}"}
