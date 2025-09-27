from pydantic import BaseModel


class LLMRank(BaseModel):
    """
    Model for the LLM to fill out with ranking information.
    Contains only the fields that should be populated by the LLM.
    """

    reason: str
    score: int
