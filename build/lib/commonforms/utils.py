from __future__ import annotations
from typing import Literal
from pydantic import BaseModel
from dataclasses import dataclass
from PIL import Image


class BoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float

    @classmethod
    def from_yolo(cls, cx: float, cy: float, w: float, h: float) -> BoundingBox:
        return cls(x0=cx - w / 2, y0=cy - h / 2, x1=cx + w / 2, y1=cy + h / 2)


class Widget(BaseModel):
    widget_type: Literal[
        "TextBox",
        "ChoiceButton",
        "Signature",
    ]
    bounding_box: BoundingBox
    page: int


@dataclass
class Page:
    image: Image.Image
    width: float
    height: float
