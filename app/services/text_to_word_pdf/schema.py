from typing import Literal

from app.services.documents import DocumentInputs


class Inputs(DocumentInputs):
    mode: Literal["direct"] = "direct"
