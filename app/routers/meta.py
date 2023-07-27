from fastapi import APIRouter
from app.utils.info import get_lcwc_version

router = APIRouter(
    prefix="/meta",
    tags=["meta"],
    responses={404: {"description": "Not found"}},
)


@router.get("/stats")
async def stats():
    """Returns various statistics about the API"""

    data = {"lcwc_version": get_lcwc_version()}

    return data
