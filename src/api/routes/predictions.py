from fastapi import APIRouter, Depends, HTTPException

from src.api.main import get_framework
from src.api.schemas.requests import OutcomeReportRequest, PredictionRequest
from src.api.schemas.responses import PredictionResponse
from src.core import ABTestFramework

