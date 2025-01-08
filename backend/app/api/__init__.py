"""API package for the application."""

from fastapi import APIRouter

router = APIRouter()

from . import tasks, workflows  # noqa 