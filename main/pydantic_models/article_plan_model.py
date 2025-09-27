from pydantic import BaseModel, Field


class ArticlePlan(BaseModel):
    daily_summary: str = Field(
        description="A brief overview of the day's most significant developments (2-3 sentences)"
    )
    top_stories: list[str] = Field(
        description="List of 3-5 key stories to cover, each with a brief description of why it's important"
    )
    structure: list[str] = Field(
        description="List of section headings that outline the summary's structure, organized by story importance"
    )
