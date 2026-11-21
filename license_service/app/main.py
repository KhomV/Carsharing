from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.endpoints.license_router import license_router


app = FastAPI(title="Carsharing Driver License Verification")
app.include_router(license_router, prefix="/api")


@app.exception_handler(RequestValidationError)
async def validation_error(_request: Request, error: RequestValidationError) -> JSONResponse:
    details = [
        {"loc": item["loc"], "msg": item["msg"], "type": item["type"]}
        for item in error.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": details})
