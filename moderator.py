from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL
from vector_store import get_similar_examples

client = Groq(api_key=GROQ_API_KEY)

def classify_message(message: str) -> str:
    """
    Classifies a Telegram message as SAFE or BAN.
    
    Args:
        message: The text content of the Telegram message
        
    Returns:
        "BAN" if the message is a scam/spam, "SAFE" otherwise
    """
    examples = get_similar_examples(message)
    system_prompt = """
    You are a moderator for Telegram group chats.
    Your job is to classify messages as SAFE or BAN.
    You only need to respond: SAFE or BAN, no explanation or punctuation needed.
    BAN only if you are absolutely sure, default to SAFE otherwise.

    BAN if the message contains:
    - Financial scams (fake giveaways, guaranteed returns, investment schemes)
    - Pornographic content, sexual solicitation, or links to adult content
    - Obvious spam (unsolicited mass advertising, repeated promotional messages)
    - Academic cheating services (assignment help, homework for hire)
    - Deliberate typos or character substitutions to evade filters (e.g. "gi ving", "stiII", "v!rg!n!ty")
    - Links to unknown suspicious domains promising rewards, services or money

    Important:
    Not all typos are a deliberate attempt to evade filters and account for the fact that typos happen very frequently in day-to-day texting.
    Account for commonly used short-forms of words.
    Evaluate the text carefully before arriving at a conclusion, considering context and intent if possible.
    If a message contains purely typos and does not contain any malicious intent (as the ones stated above under BAN categories), it is not an indicator of a deliberate act of using typos to evade filters.

    SAFE if the message contains:
    - Normal conversation of any topic (health, finance, technology)
    - Legitimate lost and found posts
    - Legitimate job or recruitment posts (even if they mention blockchain, AI, crypto, or have deadlines)
    - Links to well-known legitimate platforms (github.com, youtube.com, google.com, news sites, social media)
    - Questions, discussions, or sharing of information on any topic
    - People expressiong opinions on topics of any sorts
    - Satire
    - Anything that is not obviously a scam or spam

    Here are some examples for your reference: {examples}
    """

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt.format(examples=examples)},
            {"role": "user", "content": f"<message>{message}</message>"}
        ]
    )

    result = response.choices[0].message.content.strip().upper()
    if result not in ["SAFE", "BAN"]:
        return "SAFE"
    return result