"""Seed sample hospitals, doctors and demo accounts. Safe to run more than once.

All hospitals and doctors below are FICTIONAL sample data for the demo.
Run from backend/:  python scripts/seed.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models import Doctor, Hospital, User, UserRole  # noqa: E402

HOSPITALS = [
    ("Sunrise Skin & Wellness Clinic", "Mohali", "Sector 70, Mohali, Punjab"),
    ("CityCare Multispeciality Hospital", "Chandigarh", "Sector 34, Chandigarh"),
    ("Lotus Dermatology Centre", "New Delhi", "Greater Kailash I, New Delhi"),
    ("Riverside General Hospital", "Ludhiana", "Ferozepur Road, Ludhiana, Punjab"),
]

# (name, specialty, hospital, bio)
DOCTORS = [
    ("Dr. Anika Mehta", "Dermatologist", "Sunrise Skin & Wellness Clinic",
     "Consultant dermatologist focusing on acne, eczema and pigmentation disorders."),
    ("Dr. Rohan Kapoor", "Dermatologist", "CityCare Multispeciality Hospital",
     "Clinical dermatology and dermoscopy of pigmented lesions."),
    ("Dr. Simran Gill", "Dermatologist", "Riverside General Hospital",
     "General and paediatric dermatology."),
    ("Dr. Farah Siddiqui", "Dermatologist", "Lotus Dermatology Centre",
     "Skin of colour, psoriasis and chronic inflammatory skin disease."),
    ("Dr. Vikram Rao", "Dermato-oncologist", "CityCare Multispeciality Hospital",
     "Skin cancer screening, melanoma and non-melanoma skin cancer management."),
    ("Dr. Meera Iyer", "Dermato-oncologist", "Lotus Dermatology Centre",
     "Early detection of skin cancer and mole mapping."),
    ("Dr. Arjun Bhatia", "Dermatologic Surgeon", "Sunrise Skin & Wellness Clinic",
     "Excision of suspicious lesions, biopsies and Mohs-style surgery."),
    ("Dr. Kavya Nair", "Dermatologic Surgeon", "Lotus Dermatology Centre",
     "Surgical dermatology and lesion removal."),
    ("Dr. Harpreet Sandhu", "General Physician", "Riverside General Hospital",
     "Primary care; first point of contact and referral for skin concerns."),
    ("Dr. Neha Verma", "General Physician", "Sunrise Skin & Wellness Clinic",
     "Family medicine and minor skin conditions."),
]

DEMO_USERS = [
    # (name, email, password, role)
    ("Demo Patient", "patient@skintriage.app", "Demo@1234", UserRole.patient),
    ("Dr. Anika Mehta", "doctor@skintriage.app", "Doctor@1234", UserRole.doctor),
    ("Admin", "admin@skintriage.app", "Admin@1234", UserRole.admin),
]


def main() -> None:
    db = SessionLocal()
    try:
        hospitals: dict[str, Hospital] = {}
        for name, city, address in HOSPITALS:
            h = db.scalar(select(Hospital).where(Hospital.name == name))
            if not h:
                h = Hospital(name=name, city=city, address=address)
                db.add(h)
            hospitals[name] = h
        db.flush()

        for name, specialty, hospital, bio in DOCTORS:
            if not db.scalar(select(Doctor).where(Doctor.name == name)):
                db.add(Doctor(name=name, specialty=specialty, bio=bio,
                              hospital_id=hospitals[hospital].id))
        db.flush()

        for name, email, password, role in DEMO_USERS:
            if not db.scalar(select(User).where(User.email == email)):
                db.add(User(name=name, email=email, role=role,
                            password_hash=hash_password(password)))
        db.flush()

        # Link the demo doctor login to Dr. Anika Mehta's directory profile
        doc_user = db.scalar(select(User).where(User.email == "doctor@skintriage.app"))
        doc = db.scalar(select(Doctor).where(Doctor.name == "Dr. Anika Mehta"))
        if doc and doc_user and doc.user_id is None:
            doc.user_id = doc_user.id

        db.commit()
        print(f"✅ Seeded: {len(HOSPITALS)} hospitals, {len(DOCTORS)} doctors, {len(DEMO_USERS)} demo users")
        for _, email, password, role in DEMO_USERS:
            print(f"   {role.value:8} {email}  /  {password}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
