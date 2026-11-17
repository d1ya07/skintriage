from pydantic import BaseModel


class AdminStats(BaseModel):
    users_by_role: dict[str, int]
    active_users: int
    hospitals: int
    doctors: int
    appointments_by_status: dict[str, int]
    triage_results: int
