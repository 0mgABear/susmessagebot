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

    BAN if the message contains:
    - Financial scams (e.g. fake giveaways)
    - Pornographic content or links
    - Obvious promotion of suspicious accounts
    - Obvious spam (unsolicited promotions and advertising)
    - Academic help / cheating services
    - Deliberate typos or character substitutions to evade filters (e.g. "gi ving", "stiII", "v!rg!n!ty")

    SAFE if the message contains:
    - Normal conversation
    - Questions and/or discussions about any topic
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