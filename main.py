from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel, Field, Session, create_engine, select
from datetime import date, timedelta
from typing import Optional

DATABASE_URL = "postgresql://user:password@host:port/dbname"  # ใส่ของจริงใน Render

engine = create_engine(DATABASE_URL, echo=True)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --------------------
# MODEL
# --------------------
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


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


# --------------------
# ROUTE แสดงหน้า
# --------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request, session: Session = Depends(get_session)):
    farms = session.exec(select(Farm)).all()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "farms": farms
    })


# --------------------
# ROUTE เพิ่มข้อมูล
# --------------------
@app.post("/add")
def add_farm(
    farmer_name: str = Form(...),
    variety: str = Form(...),
    area: float = Form(...),
    price_per_ton: float = Form(...),
    plant_date: date = Form(...),
    session: Session = Depends(get_session)
):
    expected_yield = area * 1.5        # สมมุติ 3 ตันต่อไร่
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