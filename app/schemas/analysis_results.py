from pydantic import BaseModel


class ReportBase(BaseModel):
    title: str
    algorithm: str
    description: str
    result_summary: str


class ReportCreate(ReportBase):
    pass


class ReportOut(ReportBase):
    id: int
    user: str
    created_at: str
    hidden: bool

    class Config:
        orm_mode = True
