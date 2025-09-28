# Goal: Refine article creation by integrating LLM Router
- Make the model cite the URLs for the tweets it uses 
    - I should also verify that the tweet ids/links are valid and toss any that aren't
- Refine ranking and article generation prompt for reasoning models
- Try experimenting with gpt-5, gemini 2.5 flash, gemini 2.5 pro for ranking and article creation
    - Consider setting up promptfoo for testing/comparing
- Pick models for ranking and article gen and make prompt solid

# Goal: Add past day's articles for extra context
- Add up the the past x day's articles if they exist
- If multiple exist, pick the last based on time

# Goal: Make this very easily runnable by others 
- Give 1 command that checks if values are set, if they aren't, it prompts users to set them and saves them to the right place
- Update Readme to walk users through getting API keys for twitter, LLM Router and (optionally) voice creation (Eleven Labs?)


# Milestone: Basic project is ready!
- Let Wak and Sassal know
- Showcase citations and how LLMs are good are summarizing based on context they have been given


# Goal: Upgrade with podcast 
- Create a new llm prompt that turns articles into podcasts
- Use a voice model api (Eleven labs?) to send the text and get back an audio file