from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, Float, Date, String
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import date, timedelta
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ================= MODEL =================
class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True)
    farmer_name = Column(String)
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

    total_area = sum(f.area for f in farms)
    total_income = sum(f.expected_income for f in farms)

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
    farmer_name: str = Form(...),
    area: float = Form(...),
    price_per_ton: float = Form(...),
    plant_date: date = Form(...)
):
    db = SessionLocal()

    expected_yield = area * 1.5
    expected_income = expected_yield * price_per_ton
    harvest_date = plant_date + timedelta(days=90)

    farm = Farm(
        farmer_name=farmer_name,
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

# ================= DASHBOARD =================
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, month: int = None):
    db = SessionLocal()
    farms = db.query(Farm).all()

    total_area = sum(f.area for f in farms)
    total_yield = sum(f.expected_yield for f in farms)
    total_income = sum(f.expected_income for f in farms)

    # ===== คำนวณพื้นที่ที่จะขุดในเดือนที่เลือก =====
    harvest_area_month = 0
    if month:
        harvest_area_month = sum(
            f.area for f in farms if f.harvest_date.month == month
        )

    db.close()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "total_area": total_area,
        "total_yield": total_yield,
        "total_income": total_income,
        "harvest_area_month": harvest_area_month,
        "selected_month": month
    })