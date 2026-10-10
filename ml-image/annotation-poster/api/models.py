"""Contrat versionné des prédictions et des décisions humaines."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

Gender = Literal['female', 'male', 'unknown']
Age = Literal['0-2', '3-9', '10-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70+', 'unknown']


class Model(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False, str_strip_whitespace=True)


class Face(Model):
    id: str = Field(min_length=1, max_length=100)
    bbox: tuple[float, float, float, float]
    gender: Gender | None = None
    age_range: Age | None = None


class Prediction(Face):
    detection_confidence: float | None = Field(default=None, ge=0, le=1)
    provenance: str = 'trailer_match'


class Decisions(Model):
    bbox: bool = False
    gender: bool = False
    age_range: bool = False


class Annotation(Face):
    source_prediction_id: str | None = None
    deleted: bool = False
    reviewed: Decisions = Field(default_factory=Decisions)
    note: str = Field(default='', max_length=2000)


class Review(Model):
    revision: int = Field(default=0, ge=0)
    image_sha256: str
    annotator: str = Field(min_length=1, max_length=100)
    status: Literal['draft', 'validated'] = 'draft'
    complete: bool = False
    annotations: list[Annotation] = Field(max_length=2000)
    updated_at: str | None = None
