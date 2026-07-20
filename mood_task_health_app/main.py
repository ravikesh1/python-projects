from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

from .database import create_tables
from .routers import meals, mood, tasks

app = FastAPI(title="Mood Task & Health App")

BASE_DIR = os.path.dirname(__file__)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

app.include_router(mood.router)
app.include_router(tasks.router)
app.include_router(meals.router)


@app.on_event("startup")
def on_startup():
    create_tables()


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/tasks", response_class=HTMLResponse)
def tasks_page(request: Request):
    return templates.TemplateResponse(request, "tasks.html")


@app.get("/meals", response_class=HTMLResponse)
def meals_page(request: Request):
    return templates.TemplateResponse(request, "meals.html")
