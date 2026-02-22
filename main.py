import os
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel, Field, Session, create_engine, select
from datetime import date, timedelta
from typing import Optional

# -------------------------
# DATABASE (ดึงจาก Render)
# -------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL, echo=True)

app = FastAPI()
templates = Jinja2Templates(directory="templates")


# -------------------------
# MODEL
# -------------------------
class Farm(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    farmer_name: str
    variety: str
    area: float
    price_per_ton: float
    expected_yield: float
    expected_income: float
    plant_date: date
    harvest_date: date


def get_session():
    with Session(engine) as session:
        yield session


# -------------------------
# CREATE TABLE ON START
# -------------------------
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


# -------------------------
# HOME PAGE
# -------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request, session: Session = Depends(get_session)):
    farms = session.exec(select(Farm)).all()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "farms": farms
    })


# -------------------------
# ADD DATA
# -------------------------
@app.post("/add")
def add_farm(
    farmer_name: str = Form(...),
    variety: str = Form(...),
    area: float = Form(...),
    price_per_ton: float = Form(...),
    plant_date: date = Form(...),
    session: Session = Depends(get_session)
):
    expected_yield = area * 3
    expected_income = expected_yield * price_per_ton
    harvest_date = plant_date + timedelta(days=90)

    farm = Farm(
        farmer_name=farmer_name,
        variety=variety,
        area=area,
        price_per_ton=price_per_ton,
        expected_yield=expected_yield,
        expected_income=expected_income,
        plant_date=plant_date,
        harvest_date=harvest_date
    )

    session.add(farm)
    session.commit()

    return RedirectResponse("/", status_code=303)