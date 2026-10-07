from typing import Optional

from pydantic import BaseModel

class Response(BaseModel):
    query: str
    response: Optional[str] = None