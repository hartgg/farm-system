import os
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import Query
from sqlalchemy import or_
from sqlmodel import SQLModel, Field, Session, create_engine, select
from datetime import date, timedelta
from typing import Optional

# -------------------------
# DATABASE
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
# DASHBOARD PAGE
# -------------------------
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, session: Session = Depends(get_session)):
    farms = session.exec(select(Farm)).all()
    return templates.TemplateResponse("dashboard.html", {
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
    expected_yield = area * 1.5
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

    return RedirectResponse("/dashboard", status_code=303)


# -------------------------
# DELETE
# -------------------------
@app.get("/delete/{farm_id}")
def delete_farm(farm_id: int, session: Session = Depends(get_session)):
    farm = session.get(Farm, farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    session.delete(farm)
    session.commit()

    return RedirectResponse("/dashboard", status_code=303)


# -------------------------
# EDIT PAGE
# -------------------------
@app.get("/edit/{farm_id}", response_class=HTMLResponse)
def edit_page(farm_id: int, request: Request, session: Session = Depends(get_session)):
    farm = session.get(Farm, farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    return templates.TemplateResponse("edit.html", {
        "request": request,
        "farm": farm
    })


# -------------------------
# UPDATE
# -------------------------
@app.post("/update/{farm_id}")
def update_farm(
    farm_id: int,
    farmer_name: str = Form(...),
    variety: str = Form(...),
    area: float = Form(...),
    price_per_ton: float = Form(...),
    plant_date: date = Form(...),
    session: Session = Depends(get_session)
):
    farm = session.get(Farm, farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    farm.farmer_name = farmer_name
    farm.variety = variety
    farm.area = area
    farm.price_per_ton = price_per_ton
    farm.plant_date = plant_date

    farm.expected_yield = area * 3
    farm.expected_income = farm.expected_yield * price_per_ton
    farm.harvest_date = plant_date + timedelta(days=90)

    session.add(farm)
    session.commit()

    return RedirectResponse("/dashboard", status_code=303)

# ======================
# ค้นหาตามชื่อ
# ======================
@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    search: str = Query(None),
    session: Session = Depends(get_session)
):
    query = select(Farm)

    if search:
        query = query.where(Farm.farmer_name.contains(search))

    farms = session.exec(query).all()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "farms": farms,
        "search": search
    })


# ======================
# หน้าแก้ไข
# ======================
@app.get("/edit/{farm_id}", response_class=HTMLResponse)
def edit_page(
    farm_id: int,
    request: Request,
    session: Session = Depends(get_session)
):
    farm = session.get(Farm, farm_id)
    return templates.TemplateResponse("edit.html", {
        "request": request,
        "farm": farm
    })


# ======================
# บันทึกการแก้ไข
# ======================
@app.post("/edit/{farm_id}")
def update_farm(
    farm_id: int,
    farmer_name: str = Form(...),
    variety: str = Form(...),
    area: float = Form(...),
    price_per_ton: float = Form(...),
    plant_date: date = Form(...),
    session: Session = Depends(get_session)
):
    farm = session.get(Farm, farm_id)

    farm.farmer_name = farmer_name
    farm.variety = variety
    farm.area = area
    farm.price_per_ton = price_per_ton
    farm.plant_date = plant_date

    farm.expected_yield = area * 3
    farm.expected_income = farm.expected_yield * price_per_ton
    farm.harvest_date = plant_date + timedelta(days=90)

    session.add(farm)
    session.commit()

    return RedirectResponse("/", status_code=303)


# ======================
# ลบข้อมูล
# ======================
@app.get("/delete/{farm_id}")
def delete_farm(farm_id: int, session: Session = Depends(get_session)):
    farm = session.get(Farm, farm_id)
    session.delete(farm)
    session.commit()
    return RedirectResponse("/", status_code=303)