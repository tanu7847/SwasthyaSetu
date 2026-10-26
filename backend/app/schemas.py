from pydantic import BaseModel, Field

from typing import Optional

class RegisterIn(BaseModel):
    email: str
    password: str = Field(min_length=10, max_length=128)
    role: str = "patient"
    language: str = "en"
    display_name: str = Field(min_length=1, max_length=100)

class LoginIn(BaseModel):
    email: str
    password: str

class SymptomIn(BaseModel):
    symptoms: str = Field(min_length=1, max_length=3000)
    duration: str = Field(default="unknown", max_length=200)
    language: str = "en"
    allergies: str = ""
    current_medications: str = ""
    consent_to_ai_processing: bool = False

class NoteDraftIn(BaseModel):
    symptoms: str = Field(min_length=1, max_length=5000)
    history: str = Field(default="", max_length=5000)
    language: str = "en"
    transcript: str = Field(default="", max_length=10000)

class EmergencyIn(BaseModel):
    symptoms: str = Field(min_length=1, max_length=3000)
    location_text: str = Field(min_length=1, max_length=500)
    callback: str = Field(default="", max_length=40)
    symptoms_happening_now: bool = True
