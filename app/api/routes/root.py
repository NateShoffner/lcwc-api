from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

TEMPLATES_DIR = "app/api/templates"


@router.get("/", response_class=HTMLResponse)
@router.get("/api", response_class=HTMLResponse)
async def root():
    with open(f"{TEMPLATES_DIR}/index.html", "r") as file:
        html_content = file.read()

    return HTMLResponse(content=html_content, status_code=200)


@router.get("/api/v1", response_class=HTMLResponse)
async def api_root():
    with open(f"{TEMPLATES_DIR}/api.html", "r") as file:
        html_content = file.read()

    return HTMLResponse(content=html_content, status_code=200)
