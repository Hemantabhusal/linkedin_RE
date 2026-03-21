from pydantic import BaseModel


class PendingProfileRow(BaseModel):
    id: int
    linkedin_url: str

