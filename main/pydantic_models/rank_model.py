from datetime import datetime
from typing import Dict, Any
from uuid import uuid4
from sqlmodel import SQLModel, Field
from pydantic_models.llm_rank_model import LLMRank


class Rank(SQLModel, table=True):
    rank_id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    tweet_id: str
    run_time: datetime
    reason: str
    score: int
    model: str | None = None
    prompt: str | None = None

    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> "Rank":
        """Create a Rank object from a database row dictionary"""
        return cls(
            rank_id=row.get("rank_id", str(uuid4())),
            tweet_id=row["tweet_id"],
            run_time=row["run_time"],
            reason=row["reason"],
            score=row["score"],
            model=row["model"],
            prompt=row["prompt"],
        )

    @classmethod
    def from_data(cls, tweet_id: str, reason: str, score: int, **kwargs) -> "Rank":
        """Create a Rank object from individual data fields with sensible defaults for optional fields"""
        return cls(
            tweet_id=tweet_id,
            run_time=datetime.now(),
            reason=reason,
            score=score,
            **kwargs,
        )

    @classmethod
    def from_llm_rank(
        cls, llm_rank: LLMRank, tweet_id: str, model: str = None, prompt: str = None
    ) -> "Rank":
        """Create a full Rank object from an LLMRank object and additional metadata"""
        return cls(
            tweet_id=tweet_id,
            run_time=datetime.now(),
            reason=llm_rank.reason,
            score=llm_rank.score,
            model=model,
            prompt=prompt,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the Rank object to a dictionary"""
        return self.model_dump()

    def __str__(self) -> str:
        """String representation of the Rank"""
        return f"Rank(id={self.rank_id}\ntweet_id={self.tweet_id}\nrun_time={self.run_time}\nreason={self.reason}\nscore={self.score}\nmodel={self.model})"
