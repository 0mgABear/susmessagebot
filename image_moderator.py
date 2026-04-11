from PIL import Image
import io
import pytesseract
from moderator import classify_message

def classify_image(image_bytes: bytes) -> str:
    """
    Classifies a Telegram image as SAFE or BAN.
    Extracts text via OCR then uses the text classifier.

    Args:
        image_bytes: Raw image bytes downloaded from Telegram

    Returns:
        "BAN" if the image is a scam/spam, "SAFE" otherwise
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.thumbnail((1200, 1200))
        text = pytesseract.image_to_string(img).strip()

        if not text:
            return "SAFE"

        return classify_message(text)

    except Exception:
        return "SAFE"