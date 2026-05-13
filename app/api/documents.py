from fastapi import APIRouter, UploadFile, File
from app.services.document_service import DocumentService

router = APIRouter()


@router.post("/upload", summary="上传本地文档")
async def upload_document(file: UploadFile = File(...)):
    result = await DocumentService.upload_document(file)
    return result


@router.post("/query", summary="查询文档内容")
async def query_document(question: str):
    result = await DocumentService.query_document(question)
    return result
