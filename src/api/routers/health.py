from fastapi import APIRouter
from src.__version__ import __version__

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/version")
def version():
    return {"version": __version__}
