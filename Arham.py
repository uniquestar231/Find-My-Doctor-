from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

def triage(problem: str) -> str:
    text = problem.lower()

    if any(word in text for word in ["chest pain", "can’t breathe", "cant breathe",
                                     "difficulty breathing", "severe bleeding",
                                     "passed out", "unconscious"]):
        return "Your symptoms sound serious. You should go to urgent care or the emergency room right away."

    if any(word in text for word in ["seizure", "migraine", "bad headache",
                                     "numbness", "dizzy", "dizziness"]):
        return "You should see a neurologist for these symptoms."

    if any(word in text for word in ["palpitations", "heart racing",
                                     "shortness of breath", "heart problem",
                                     "heart issues"]):
        return "You should see a cardiologist for these symptoms."

    if any(word in text for word in ["stomach", "belly", "abdomen",
                                     "nausea", "vomit", "vomiting", "diarrhea"]):
        return "You can start with a primary care doctor or a gastroenterologist."

    return "You can start with a primary care doctor. If it gets worse or feels like an emergency, go to urgent care."


app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def form_page(request: Request):
    return templates.TemplateResponse(
        "form.html",
        {"request": request, "result": None}
    )


@app.post("/", response_class=HTMLResponse)
async def submit_form(
    request: Request,
    name: str = Form(...),
    address: str = Form(...),
    problem: str = Form(...)
):
    recommendation = triage(problem)
    result = {
        "name": name,
        "address": address,
        "problem": problem,
        "recommendation": recommendation,
    }
    return templates.TemplateResponse(
        "form.html",
        {"request": request, "result": result}
    )