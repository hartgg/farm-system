import os
from datetime import date, timedelta
from typing import Optional

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from sqlmodel import SQLModel, Field, Session, create_engine, select
import pandas as pd
import io

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ================= DATABASE =================

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=False)


class Farm(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    farmer_name: str
    phone: str
    area_rai: float
    plant_date: date
    harvest_date: date
    expected_yield: float
    status: str = "กำลังปลูก"


def create_db():
    SQLModel.metadata.create_all(engine)


create_db()


# ================= HELPER =================

def calculate_status(harvest_date):
    today = date.today()
    if today < harvest_date:
        return "กำลังปลูก"
    elif today == harvest_date:
        return "รอขุด"
    else:
        return "ขุดแล้ว"


# ================= ROUTES =================

@app.get("/", response_class=HTMLResponse)
def home(request: Request, search: Optional[str] = None):
    with Session(engine) as session:
        farms = session.exec(select(Farm)).all()

    if search:
        farms = [
            f for f in farms
            if search.lower() in f.farmer_name.lower()
            or search in f.phone
        ]

    # รวมผลผลิตรายเดือน
    monthly = {}
    for f in farms:
        month = f.harvest_date.strftime("%Y-%m")
        monthly[month] = monthly.get(month, 0) + f.expected_yield

    return templates.TemplateResponse("index.html", {
        "request": request,
        "farms": farms,
        "monthly": monthly
    })


@app.get("/add", response_class=HTMLResponse)
def add_form(request: Request):
    return templates.TemplateResponse("add.html", {"request": request})


@app.post("/add")
def add_farm(
    farmer_name: str = Form(...),
    phone: str = Form(...),
    area_rai: float = Form(...),
    plant_date: date = Form(...)
):
    harvest_date = plant_date + timedelta(days=90)
    expected_yield = area_rai * 1.5
    status = calculate_status(harvest_date)

    farm = Farm(
        farmer_name=farmer_name,
        phone=phone,
        area_rai=area_rai,
        plant_date=plant_date,
        harvest_date=harvest_date,
        expected_yield=expected_yield,
        status=status
    )

    with Session(engine) as session:
        session.add(farm)
        session.commit()

    return RedirectResponse("/", status_code=303)


@app.get("/delete/{farm_id}")
def delete_farm(farm_id: int):
    with Session(engine) as session:
        farm = session.get(Farm, farm_id)
        if farm:
            session.delete(farm)
            session.commit()
    return RedirectResponse("/", status_code=303)


@app.get("/edit/{farm_id}", response_class=HTMLResponse)
def edit_form(request: Request, farm_id: int):
    with Session(engine) as session:
        farm = session.get(Farm, farm_id)
    return templates.TemplateResponse("edit.html", {
        "request": request,
        "farm": farm
    })


@app.post("/edit/{farm_id}")
def edit_farm(
    farm_id: int,
    farmer_name: str = Form(...),
    phone: str = Form(...),
    area_rai: float = Form(...),
    plant_date: date = Form(...)
):
    with Session(engine) as session:
        farm = session.get(Farm, farm_id)
        farm.farmer_name = farmer_name
        farm.phone = phone
        farm.area_rai = area_rai
        farm.plant_date = plant_date
        farm.harvest_date = plant_date + timedelta(days=90)
        farm.expected_yield = area_rai * 1.5
        farm.status = calculate_status(farm.harvest_date)
        session.add(farm)
        session.commit()

    return RedirectResponse("/", status_code=303)


@app.get("/export")
def export_excel():
    with Session(engine) as session:
        farms = session.exec(select(Farm)).all()

    data = [{
        "ชื่อ": f.farmer_name,
        "เบอร์": f.phone,
        "พื้นที่ (ไร่)": f.area_rai,
        "วันปลูก": f.plant_date,
        "วันขุด": f.harvest_date,
        "ผลผลิต (ตัน)": f.expected_yield,
        "สถานะ": f.status
    } for f in farms]

    df = pd.DataFrame(data)
    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=farm_data.xlsx"
        }
    )