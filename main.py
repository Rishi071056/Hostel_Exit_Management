from fastapi import FastAPI
from backend.crud import get_all_students
from backend.routers.student import router as student_router
from backend.routers.warden import router as warden_router
from backend.routers.guard import router as guard

app = FastAPI()


@app.get("/students")
async def root():
    return get_all_students()

app.include_router(student_router)


app.include_router(
    warden_router,
    prefix="/warden"
)
app.include_router(
    guard,
    prefix="/guard",
    tags=["Guard"]
)