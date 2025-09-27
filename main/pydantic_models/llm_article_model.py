from pydantic import BaseModel, Field


class LLMArticle(BaseModel):
    """
    Model for the LLM to fill out with article information.
    Contains only the fields that should be populated by the LLM.
    """

    content: str = Field(description="The full content of the news article")
    summary: str = Field(description="A short summary of the article")
    daily_summary: str = Field(
        description="A brief overview of the day's most significant developments"
    )
    title: str = Field(description="The title of the news article")
    top_stories: list[str] = Field(
        description="List of key stories covered in the article"
    )


class LLMArticleV2(BaseModel):
    """
    Try making the LLM generate the article in paragraphs that we can stich together with relevant citations already connected
    """

    content: list[dict[str, str | list[str]]] = Field(
        description="""A list of JSON dictionaries. Each of these dictionaries has the following key/value pairs. 
    1. key:"paragraph_text", value: The string text of a paragraph of the article.
    2. key:"relevant_tweet_ids_list", value: a python list of the string UUID tweet ids relevant to the paragraph you just created. All relevant tweet ids that the paragraph references or uses information from must be included here!
    """
    )
    summary: str = Field(
        description="A short summary of all of the article's paragraphs"
    )
    daily_summary: str = Field(
        description="A brief overview of the day's most significant developments"
    )
    title: str = Field(description="The title of the news article")
    top_stories: list[str] = Field(
        description="List of key stories covered in the article"
    )
