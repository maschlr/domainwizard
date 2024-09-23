import anthropic

from ..config import config

# Initialize Anthropic client
aclient = anthropic.AsyncAnthropic(api_key=config["ANTHROPIC_API_KEY"])
client = anthropic.Anthropic(api_key=config["ANTHROPIC_API_KEY"])


async def get_keywordlist(prompt: str) -> list[str]:
    response = await aclient.beta.prompt_caching.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": (
                    "You are an expert AI assistant tasked with generating a list of keywords from a given prompt. "
                    "You are part of an application that helps people find domain names for their website. "
                    "The prompt that you will be given describes a website. If the description is not complete, make informed assumptions"
                    " about the purpose, the target audience and all other relevant points."
                    " The keywords will be used for a search query of domain names."
                    "Your goal is to provide ONLY a list of keywords and NOTHING ELSE. Provide the 10 most relevant keywords."
                    "Sort the keywords by relevance to the prompt, starting with the most relevant."
                ),
                "cache_control": {"type": "ephemeral"},
            },
        ],
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return response.content[0].text.splitlines()


async def filter_domains(domains: list[str], prompt: str) -> list[str]:
    response = await aclient.beta.prompt_caching.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": (
                    "You are an AI assistant tasked with filtering a list of domain names. "
                    "You will be given a prompt and a list of domain names. "
                    "The prompt describes a website. If the description is not complete, make informed assumptions"
                    " about the purpose, the target audience and all other relevant points."
                    " Filter the list of domain names to only include those that are relevant to the prompt. "
                    "Also, sort the domains by quality. The most relevant domain names should be at the top of the list. "
                    "Shorter domains are better than longer domains. Domains that contain numbers at the end are of low quality."
                    "Your goal is to provide ONLY a list of 50 domains and NOTHING ELSE. "
                    "All domains in your output must be from the list of domains that you are given in the users intput."
                ),
                "cache_control": {"type": "ephemeral"},
            },
            {"type": "text", "text": f"The prompt is:\n\n{prompt}"},
        ],
        messages=[
            {
                "role": "user",
                "content": "List of domains to filter:\n\n" + "\n".join(domains),
            }
        ],
    )

    return response.content[0].text.splitlines()


async def rate_domain(domain: str, quality_score: int, prompt: str) -> int:
    response = await aclient.beta.prompt_caching.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": (
                    "You are an AI assistant tasked with rating a domain name. "
                    "You will be given a domain name, a quality score and a prompt. "
                    "The prompt desribes the website that the domain is for. "
                    "The quality score is calculated based on price, pageviews, valuation, monthly parking revenue and other technical factors."
                    "Rate the domain name from 1 to 100 where 100 is the highest quality. "
                    "A domain name is a good fit if it is short, memorable and easy to spell. "
                    "It should also be relevant to the prompt. "
                    "The best domain names are short, memorable and easy to spell. "
                    "The best domain names are relevant to the prompt. "
                    "The best domain names are easy to pronounce. "
                    "The best domain names are easy to remember. "
                    "The best domain names are easy to type. "
                    "The best domain names are easy to find. "
                    "Output ONLY the rating as a number between 1 (low quality) and 100 (high quality) and NOTHING ELSE."
                ),
                "cache_control": {"type": "ephemeral"},
            },
        ],
        messages=[
            {
                "role": "user",
                "content": f"The domain name is: {domain}\n\nThe quality score is: {quality_score}\n\nThe prompt is: {prompt}",
            },
        ],
    )

    return int(response.content[0].text)


def get_summary(description: str) -> str:
    response = client.beta.prompt_caching.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=30,
        system=[
            {
                "type": "text",
                "text": (
                    "You are an AI assistant tasked with summarizing a website description. "
                    "The summary will be used as a heading for the description. "
                    "Keep it short and to the point. Your answer should be a single line of text and NOTHING ELSE."
                ),
                "cache_control": {"type": "ephemeral"},
            },
        ],
        messages=[
            {"role": "user", "content": f"The description is: {description}"},
        ],
    )

    return response.content[0].text
