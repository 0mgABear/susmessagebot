from PIL import Image, ImageEnhance, ImageOps
import io
import pytesseract
from moderator import classify_message
import logging

def _preprocess_image(img: Image.Image) -> Image.Image:
    """Preprocess image for better OCR accuracy."""
    # Convert to grayscale
    img = img.convert('L')
    
    # Detect if dark background — invert if so
    avg_brightness = sum(img.getdata()) / len(img.getdata())
    if avg_brightness < 128:
        img = ImageOps.invert(img)
    
    # Boost contrast
    img = ImageEnhance.Contrast(img).enhance(2.0)
    
    # Threshold to pure B&W
    img = img.point(lambda x: 0 if x < 128 else 255)
    
    return img

def classify_image(image_bytes: bytes) -> str:
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = _preprocess_image(img)
        text = pytesseract.image_to_string(img, config='--psm 6').strip()
        logging.info(f"OCR extracted text: {text[:200]}")

        if not text:
            logging.info("No text found in image, returning SAFE")
            return "SAFE"

        logging.info("Calling classify_message...")
        result = classify_message(text)
        logging.info(f"classify_message returned: {result}")
        return result

    except Exception as e:
        logging.error(f"Image classification error: {e}")
        return "SAFE"