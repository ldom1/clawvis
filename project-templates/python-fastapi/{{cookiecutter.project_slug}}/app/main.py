from fastapi import FastAPI

app = FastAPI(title="{{cookiecutter.project_name}}")


@app.get("/health")
def health():
    return {"ok": True, "project": "{{cookiecutter.project_slug}}"}
