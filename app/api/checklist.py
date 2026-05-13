from fastapi import APIRouter
from app.models.schemas import ChecklistRequest, ChecklistResponse
from app.services.checklist_service import ChecklistService

router = APIRouter()


@router.post("", response_model=ChecklistResponse, summary="生成出门清单")
async def generate_checklist(request: ChecklistRequest):
    items = await ChecklistService.build_checklist(request)
    return ChecklistResponse(items=items)
