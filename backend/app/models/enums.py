import enum


class UserRole(str, enum.Enum):
    patient = "patient"
    doctor = "doctor"
    admin = "admin"


class AppointmentStatus(str, enum.Enum):
    booked = "booked"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"


class UrgencyLevel(str, enum.Enum):
    low = "low"
    moderate = "moderate"
    high = "high"
