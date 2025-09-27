from datetime import datetime
from typing import Dict, Any
from uuid import uuid4
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON
from pydantic_models.llm_article_model import LLMArticle


class Article(SQLModel, table=True):
    article_id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    title: str = Field(description="The title of the news article")
    content: str = Field(description="The full content of the news article")
    summary: str = Field(description="A short summary of the article")
    daily_summary: str = Field(
        description="A brief overview of the day's most significant developments"
    )
    top_stories: list[str] = Field(
        sa_column=Column(JSON), description="List of key stories covered in the article"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="When the article was generated"
    )
    model: str | None = None
    prompt: str | None = None

    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> "Article":
        """Create an Article object from a database row dictionary"""
        return cls(
            article_id=row.get("article_id", str(uuid4())),
            title=row["title"],
            content=row["content"],
            summary=row["summary"],
            daily_summary=row["daily_summary"],
            top_stories=row["top_stories"],
            created_at=row["created_at"],
            model=row.get("model"),
            prompt=row.get("prompt"),
        )

    @classmethod
    def from_llm_article(
        cls, llm_article: LLMArticle, model: str = None, prompt: str = None
    ) -> "Article":
        """Create a full Article object from an LLMArticle object and additional metadata"""
        return cls(
            title=llm_article.title,
            content=llm_article.content,
            summary=llm_article.summary,
            daily_summary=llm_article.daily_summary,
            top_stories=llm_article.top_stories,
            model=model,
            prompt=prompt,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the Article object to a dictionary"""
        return self.model_dump()

    def __str__(self) -> str:
        """String representation of the Article"""
        return f"Article(id={self.article_id}\ntitle={self.title}\ncreated_at={self.created_at}\nmodel={self.model})"
