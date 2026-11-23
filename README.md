# SkinTriage

**AI-based skin condition triage and referral system.** Upload a photo of a skin lesion, get a calibrated suggestion of the lesion type, an urgency level (low, moderate or high) with the reasons behind it, and book a matching specialist in the same session.

> SkinTriage is a clinical decision-support and triage prototype built as a B.Tech CSE major project. It is **not a diagnostic tool** and has not been clinically validated. Always consult a qualified doctor.

Live demo: https://skintriage-diya.malaysiawest.cloudapp.azure.com

## Features

- **Image triage:** EfficientNet-B0 trained on HAM10000 + ISIC 2019 (24,900 images, 7 lesion classes), with temperature-scaled (calibrated) confidence
- **Rule engine:** turns model probabilities into urgency and specialist type; rules can only raise urgency (for example, melanoma probability of 25% or more always means high urgency), and every result explains why
- **Appointment booking:** doctor directory, 30-minute slots, double-booking blocked at the database level, cancellation
- **Role-based portals:** patient, doctor (sees linked scans, confirms and completes visits) and admin (users, analytics)
- **FAQ assistant:** answers platform questions; clinical and emergency questions are blocked by guardrails before they reach the language model
- **Email notifications** with calendar (.ics) invites
- **Privacy:** uploads are verified and re-encoded to strip EXIF (GPS) data; images are never public

## Results

Both models evaluated on the same test images:

| Metric | HAM10000 only | HAM10000 + ISIC 2019 |
| --- | --- | --- |
| Balanced accuracy, HAM10000 test (1,502 images) | 72.2% | 76.4% |
| Balanced accuracy, combined test (3,703 images) | 54.2% | 65.6% |
| Melanomas flagged high urgency, combined test | 41.7% | 74.0% |
| Calibration error (ECE), after scaling | | 0.016 |

## Tech stack

| Layer | Technology |
| --- | --- |
| Frontend | React, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| Backend | Python 3.12, FastAPI, SQLAlchemy, Alembic, Pydantic, JWT, bcrypt |
| Database | PostgreSQL 16 |
| ML | PyTorch, torchvision (EfficientNet-B0), scikit-learn, ONNX Runtime |
| Chatbot | Anthropic API (Claude Haiku) with rule-based guardrails |
| Deployment | Docker Compose, nginx, Caddy (HTTPS), Microsoft Azure |
| Testing | Pytest (100 tests), Vitest (16 tests) |

## Project structure

```
backend/    FastAPI app (api, services, models, schemas, ml, chatbot), Alembic migrations, tests
frontend/   React + TypeScript single-page app
ml/         Data preparation, training, ONNX export, evaluation and reports
deploy/     Caddy configuration for production
```

## Running locally

Requires Docker Desktop.

```bash
git clone https://github.com/d1ya07/skintriage.git
cd skintriage
cp .env.example .env        # then fill in the values
docker compose up -d --build
```

Open http://localhost:8080. The seed script (`backend/scripts/seed.py`) creates sample hospitals, doctors and demo accounts.

Run the backend tests:

```bash
cd backend
python -m pytest -q
```

## Datasets

- HAM10000: P. Tschandl, C. Rosendahl and H. Kittler, *Scientific Data* 5, 180161 (2018). Harvard Dataverse, doi:10.7910/DVN/DBW86T
- ISIC 2019 Challenge training data (BCN_20000, HAM10000, MSK), CC BY-NC 4.0: https://challenge.isic-archive.com/data/

The datasets are not included in this repository. Download them from the official sources above.

## Team

- **Diya Sharma** and **Radhika Sharma**, B.Tech CSE, Amity School of Engineering and Technology, Amity University Punjab, Mohali
- Supervisor: **Dr. Gurpreet Singh**, Assistant Professor
