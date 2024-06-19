from pydantic import BaseModel
from typing import List


class EmbeddingRequest(BaseModel):
    texts: List[str]
    max_length: int = 8192


class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]