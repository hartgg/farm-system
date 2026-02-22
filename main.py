from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, Float, Date
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import date, timedelta
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ================= MODEL =================
class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True)
    area = Column(Float)
    price_per_ton = Column(Float)
    expected_yield = Column(Float)
    expected_income = Column(Float)
    plant_date = Column(Date)
    harvest_date = Column(Date)

Base.metadata.create_all(bind=engine)

# ================= HOME =================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    db = SessionLocal()
    farms = db.query(Farm).all()

    total_area = sum(f.area for f in farms) if farms else 0
    total_income = sum(f.expected_income for f in farms) if farms else 0

    db.close()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "farms": farms,
        "total_area": total_area,
        "total_income": total_income
    })

# ================= ADD =================
@app.post("/add")
def add(
    area: float = Form(...),
    price_per_ton: float = Form(...),
    plant_date: date = Form(...)
):
    db = SessionLocal()

    expected_yield = area * 1.5
    expected_income = expected_yield * price_per_ton
    harvest_date = plant_date + timedelta(days=90)

    farm = Farm(
        area=area,
        price_per_ton=price_per_ton,
        expected_yield=expected_yield,
        expected_income=expected_income,
        plant_date=plant_date,
        harvest_date=harvest_date
    )

    db.add(farm)
    db.commit()
    db.close()

    return RedirectResponse("/", status_code=303)

# ================= DELETE =================
@app.get("/delete/{farm_id}")
def delete(farm_id: int):
    db = SessionLocal()
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if farm:
        db.delete(farm)
        db.commit()
    db.close()
    return RedirectResponse("/", status_code=303)

# ================= EDIT PAGE =================
@app.get("/edit/{farm_id}", response_class=HTMLResponse)
def edit_page(request: Request, farm_id: int):
    db = SessionLocal()
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    db.close()
    return templates.TemplateResponse("edit.html", {"request": request, "farm": farm})

# ================= UPDATE =================
@app.post("/update/{farm_id}")
def update(
    farm_id: int,
    area: float = Form(...),
    price_per_ton: float = Form(...),
    plant_date: date = Form(...)
):
    db = SessionLocal()
    farm = db.query(Farm).filter(Farm.id == farm_id).first()

    if farm:
        farm.area = area
        farm.price_per_ton = price_per_ton
        farm.expected_yield = area * 1.5
        farm.expected_income = farm.expected_yield * price_per_ton
        farm.plant_date = plant_date
        farm.harvest_date = plant_date + timedelta(days=90)

        db.commit()

    db.close()
    return RedirectResponse("/", status_code=303)

# ================= DASHBOARD =================
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    db = SessionLocal()
    farms = db.query(Farm).all()
    db.close()

    total_area = sum(f.area for f in farms) if farms else 0
    total_yield = sum(f.expected_yield for f in farms) if farms else 0
    total_income = sum(f.expected_income for f in farms) if farms else 0

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "total_area": total_area,
        "total_yield": total_yield,
        "total_income": total_income
    })