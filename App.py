from typing import List, Optional
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Find My Doctor")

# -------- Pydantic models --------

class SymptomInput(BaseModel):
    address: str = Field(..., min_length=3)
    problem: str = Field(..., min_length=5)

class TriageResult(BaseModel):
    can_ai_help: bool
    severity: str
    recommended_specialties: List[str]
    message: str

class Doctor(BaseModel):
    id: int
    name: str
    specialty: str
    location_zip: str
    min_fee: int
    max_fee: int
    insurance: List[str]
    works_in_team: bool
    team_name: Optional[str] = None
    next_update: str
    claim: str
    avg_rating: Optional[float] = None

class DoctorFilter(BaseModel):
    address: str
    specialty: Optional[str] = None
    insurance: Optional[str] = None
    min_budget: Optional[int] = None
    max_budget: Optional[int] = None

class RatingInput(BaseModel):
    rating: int = Field(..., ge=1, le=5)

# -------- Mock data --------

DOCTORS_DB = [
    {
        "id": 1,
        "name": "Dr. Alice Nguyen",
        "specialty": "Cardiologist",
        "location_zip": "10001",
        "min_fee": 100,
        "max_fee": 250,
        "insurance": ["Aetna", "BlueCross"],
        "works_in_team": True,
        "team_name": "HeartCare Group",
        "next_update": "2026-03-01",
        "claim": "Preventive cardiology and heart failure management.",
        "ratings": [5, 4, 5],
    },
    {
        "id": 2,
        "name": "Dr. Brian Lee",
        "specialty": "Neurologist",
        "location_zip": "10002",
        "min_fee": 120,
        "max_fee": 300,
        "insurance": ["UnitedHealth", "Aetna"],
        "works_in_team": False,
        "team_name": None,
        "next_update": "2026-02-25",
        "claim": "Specialist in migraine and seizure disorders.",
        "ratings": [4, 4],
    },
]

def avg_rating(ratings):
    return sum(ratings) / len(ratings) if ratings else None

# -------- Simple triage logic --------

def triage(problem: str) -> TriageResult:
    text = problem.lower()
    severe_words = ["chest pain", "difficulty breathing", "severe bleeding"]
    neuro_words = ["seizure", "migraine", "headache"]
    cardio_words = ["chest pain", "palpitations", "heart"]

    severe = any(w in text for w in severe_words)

    specialties = set()
    if any(w in text for w in neuro_words):
        specialties.add("Neurologist")
    if any(w in text for w in cardio_words):
        specialties.add("Cardiologist")
    if not specialties:
        specialties.add("Primary Care")

    if severe:
        return TriageResult(
            can_ai_help=False,
            severity="severe",
            recommended_specialties=list(specialties),
            message="Your symptoms may be an emergency. Go to urgent care / ER now.",
        )

    return TriageResult(
        can_ai_help=True,
        severity="mild",
        recommended_specialties=list(specialties),
        message="AI can give basic guidance. Follow up with a doctor soon.",
    )

def zip_from_address(addr: str) -> Optional[str]:
    for token in addr.split():
        if token.isdigit() and len(token) == 5:
            return token
    return None

# -------- Endpoints --------

@app.post("/triage", response_model=TriageResult)
def triage_endpoint(data: SymptomInput):
    return triage(data.problem)

@app.post("/doctors", response_model=List[Doctor])
def list_doctors(filters: DoctorFilter):
    zip_code = zip_from_address(filters.address)
    docs = []
    for d in DOCTORS_DB:
        if zip_code and d["location_zip"] != zip_code:
            continue
        if filters.specialty and d["specialty"] != filters.specialty:
            continue
        if filters.insurance and filters.insurance not in d["insurance"]:
            continue
        if filters.min_budget is not None and d["max_fee"] < filters.min_budget:
            continue
        if filters.max_budget is not None and d["min_fee"] > filters.max_budget:
            continue
        docs.append(
            Doctor(
                id=d["id"],
                name=d["name"],
                specialty=d["specialty"],
                location_zip=d["location_zip"],
                min_fee=d["min_fee"],
                max_fee=d["max_fee"],
                insurance=d["insurance"],
                works_in_team=d["works_in_team"],
                team_name=d["team_name"],
                next_update=d["next_update"],
                claim=d["claim"],
                avg_rating=avg_rating(d["ratings"]),
            )
        )
    return docs

@app.post("/doctors/{doctor_id}/rate")
def rate_doctor(doctor_id: int, payload: RatingInput):
    for d in DOCTORS_DB:
        if d["id"] == doctor_id:
            d["ratings"].append(payload.rating)
            return {"message": "Rating saved."}
    return {"error": "Doctor not found"}
