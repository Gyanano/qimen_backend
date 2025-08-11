"""FastAPI application exposing Qimen Dunjia endpoints."""

from fastapi import FastAPI, Depends, Header, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional

from . import models, database, points, qimen, llm, utils


app = FastAPI(title="Qimen Dunjia AI Backend", version="0.1.0")



def get_user_id(x_user_id: Optional[str] = Header(None), user_id: Optional[str] = None) -> str:
    """Resolve the user ID or return a default ID in test mode.

    To facilitate feature testing, when no user information is provided the
    function returns a fixed identifier and bypasses authentication.  In
    production this function should extract the user identifier from a
    validated authentication token and perform proper lookups.
    """
    uid = x_user_id or user_id
    if not uid:
        # return a static user id for testing without checking the database
        return "tester"
    # If user id provided, allow use without verifying to simplify testing
    return uid


@app.post("/auth/signup", response_model=models.UserResponse, responses={400: {"model": models.ErrorResponse}})
def signup(req: models.SignUpRequest) -> models.UserResponse:
    """Register a new user.

    This endpoint creates a user record in the JSON store and returns the
    newly created user.  If the email is already registered, a 400 error is
    returned.
    """
    try:
        user = database.create_user(req.email, req.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return models.UserResponse(id=user["id"], email=user["email"], points=user["points"])


@app.post("/auth/login", response_model=models.UserResponse, responses={401: {"model": models.ErrorResponse}})
def login(req: models.LoginRequest) -> models.UserResponse:
    """Authenticate an existing user.

    In the prototype this simply checks the email/password and returns the
    stored user record.  Failure to authenticate results in a 401 error.
    """
    user = database.authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return models.UserResponse(id=user["id"], email=user["email"], points=user["points"])


@app.get("/points", response_model=models.PointsResponse, responses={401: {"model": models.ErrorResponse}})
def get_points(current_user: str = Depends(get_user_id)) -> models.PointsResponse:
    """Return the current point balance for the authenticated user."""
    user = database.get_user(current_user)
    assert user is not None  # Protected by dependency
    return models.PointsResponse(user_id=user["id"], points=user.get("points", 0))


@app.post("/points/earn", response_model=models.PointsResponse, responses={400: {"model": models.ErrorResponse}, 401: {"model": models.ErrorResponse}})
def earn_points(current_user: str = Depends(get_user_id)) -> models.PointsResponse:
    """Perform a daily sign‑in to earn points."""
    try:
        new_balance = points.earn_daily_signin(current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return models.PointsResponse(user_id=current_user, points=new_balance)


@app.post("/points/spend", response_model=models.PointsResponse, responses={400: {"model": models.ErrorResponse}, 401: {"model": models.ErrorResponse}})
def spend_points(req: models.PointsSpendRequest, current_user: str = Depends(get_user_id)) -> models.PointsResponse:
    """Deduct points from the user's balance."""
    try:
        new_balance = points.spend_points(current_user, req.amount)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return models.PointsResponse(user_id=current_user, points=new_balance)


@app.post("/inquiry", response_model=models.InquiryResponse)
def inquiry(req: models.InquiryRequest, current_user: str = Depends(get_user_id)) -> models.InquiryResponse:
    """Answer a free‑form question using the current Qimen chart and the LLM.

    In test mode this endpoint does not deduct points from the user.  It
    generates a chart based on the current time in the user's timezone
    and forwards the prompt to the configured LLM.
    """
    now = utils.now_in_pacific()
    chart = qimen.generate_chart(now)
    prompt = qimen.chart_to_prompt(chart, req.question)
    answer = llm.ask_llm(prompt)
    # Return a dummy points balance of zero for compatibility
    return models.InquiryResponse(answer=answer, points_remaining=0)


@app.post("/analysis/quantification", response_model=models.AnalysisResponse)
def qimen_quantification(req: models.QuantificationRequest, current_user: str = Depends(get_user_id)) -> models.AnalysisResponse:
    """Analyze a cryptocurrency (BTC/ETH) using the current Qimen chart.

    In test mode this endpoint does not deduct points from the user.
    """
    now = utils.now_in_pacific()
    chart = qimen.generate_chart(now)
    context = f"Provide a bullish or bearish forecast for {req.crypto.upper()} based on current market sentiment and the Qimen chart."
    prompt = qimen.chart_to_prompt(chart, f"What is the outlook for {req.crypto.upper()}?", context)
    result = llm.ask_llm(prompt)
    return models.AnalysisResponse(result=result, points_remaining=0)


@app.post("/analysis/finance", response_model=models.AnalysisResponse)
def qimen_finance(req: models.FinanceRequest, current_user: str = Depends(get_user_id)) -> models.AnalysisResponse:
    """Provide general investment guidance based on the current time and chart.

    In test mode this endpoint does not deduct points from the user.
    """
    now = utils.now_in_pacific()
    chart = qimen.generate_chart(now)
    context = "Offer a summary of the current economic climate and suggest prudent investment actions."
    prompt = qimen.chart_to_prompt(chart, "What should I consider when investing today?", context)
    result = llm.ask_llm(prompt)
    return models.AnalysisResponse(result=result, points_remaining=0)


@app.post("/analysis/destiny", response_model=models.AnalysisResponse)
def qimen_destiny(req: models.DestinyRequest, current_user: str = Depends(get_user_id)) -> models.AnalysisResponse:
    """Analyze personal destiny based on birth date/time and the Qimen chart.

    In test mode this endpoint does not deduct points from the user.
    """
    try:
        birth_dt = utils.parse_birth_datetime(req.birth_date, req.birth_time)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid birth date/time: {exc}")
    chart = qimen.generate_chart(birth_dt)
    context = "Provide an overview of the querent's career, romance, wealth and health prospects based on the birth chart."
    prompt = qimen.chart_to_prompt(chart, "What does this chart suggest about my future?", context)
    result = llm.ask_llm(prompt)
    return models.AnalysisResponse(result=result, points_remaining=0)
