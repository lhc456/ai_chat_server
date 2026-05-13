from typing import Any


class DocumentService:
    @staticmethod
    async def upload_document(file: Any) -> dict:
        # TODO: 保存文件元数据并提取文本，后续可接入向量检索
        return {"filename": getattr(file, "filename", "unknown"), "status": "uploaded"}

    @staticmethod
    async def query_document(query: str) -> dict:
        # TODO: 实现文档问答逻辑
        return {"query": query, "answer": "这是文档问答的占位回复。"}
