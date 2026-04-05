from pydantic import BaseModel, Field


class LikeRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    post_id: int = Field(..., gt=0)


class CommentRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    post_id: int = Field(..., gt=0)
    content: str = Field(..., min_length=1, max_length=5000)
