import pytesseract
from pdf2image import convert_from_path
import re
import os
import cv2
from PIL import Image
from rapidfuzz import process, fuzz

# 🔹 Tesseract OCR and Poppler paths
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPLER_PATH = r"C:\poppler-25.07.0\Library\bin"

# 🔹 Keywords for each invoice field
FIELD_KEYWORDS = {
    "Invoice No": ["Invoice No", "Invoice #", "Invoice ID", "Bill No", "Bill #", "Ref No", "Ref ID"],
    "Invoice Date": ["Invoice Date", "Bill Date", "Date of Invoice", "Date"],
    "Due Date": ["Due Date", "Payment Due", "Payment Date"],
    "Subtotal": ["Subtotal", "Amount Before Tax", "Total Before Tax"],
    "Tax": ["Tax", "GST", "VAT", "Tax Amount"],
    "Total": ["Total Amount", "Grand Total", "Total"],
    "Currency": ["INR", "USD", "EUR", "$", "₹", "€"],
    "Vendor": ["From", "Vendor", "Supplier", "Seller"],
    "Customer": ["To", "Bill To", "Customer", "Buyer"],
}

# 🔹 Preprocess image for better OCR
def preprocess_image(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    pil_img = Image.fromarray(thresh)
    return pil_img

# 🔹 Extract text from PDF
def extract_text_from_pdf(pdf_path):
    try:
        images = convert_from_path(pdf_path, poppler_path=POPLER_PATH)
        text = ""
        for img in images:
            text += pytesseract.image_to_string(img)
        return text
    except Exception as e:
        return f"⚠️ Error reading PDF: {e}"

# 🔹 Extract text from image
def extract_text_from_image(image_path):
    try:
        preprocessed_img = preprocess_image(image_path)
        text = pytesseract.image_to_string(preprocessed_img)
        return text
    except Exception as e:
        return f"⚠️ Error reading image: {e}"

# 🔹 Extract a specific field using regex + fuzzy matching
def extract_field(text, keywords, max_chars=50):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for line in lines:
        for keyword in keywords:
            if keyword.lower() in line.lower():
                # Extract the value after the keyword
                match = re.search(rf"{keyword}[:\s\-]*([\w\s.,/#-]+)", line, re.IGNORECASE)
                if match:
                    return match.group(1).strip()[:max_chars]

        # Fuzzy match fallback
        result = process.extractOne(line, keywords, scorer=fuzz.partial_ratio)
        if result:
            match, score, _ = result
            if score > 80:
                # Try to extract a number, date, or text after the keyword
                num_match = re.search(r"\b\d+[./-]?\d*[./-]?\d*\b", line)
                if num_match:
                    return num_match.group(0)
                return line.strip()[:max_chars]
    return "Not Found"

# 🔹 Extract invoice details
def extract_invoice_details(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext in [".pdf"]:
        text = extract_text_from_pdf(file_path)
    elif ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
        text = extract_text_from_image(file_path)
    else:
        return {"Error": "Unsupported file type"}

    # Optional: clean text for consistent matching
    text = text.replace("\n\n", "\n").replace(":", " : ")

    details = {}
    for field, keywords in FIELD_KEYWORDS.items():
        details[field] = extract_field(text, keywords)

    # 🔹 Smart value corrections
    if details["Total"] == "Not Found":
        total_match = re.search(r"(?:Total|Grand Total)[:\s]*([\d,.]+)", text, re.IGNORECASE)
        if total_match:
            details["Total"] = total_match.group(1)

    if details["Invoice Date"] == "Not Found":
        date_match = re.search(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", text)
        if date_match:
            details["Invoice Date"] = date_match.group(1)

    return details
