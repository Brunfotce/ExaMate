# utils.py

import re

def format_hms(seconds):
    """Format seconds into HH:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def combine_text_for_display(parts):
    """
    Merges text and image placeholders.
    For the summary, images are represented as [IMG].
    """
    out = []
    for (ptype, content) in parts:
        if ptype == "text":
            out.append(content)
        elif ptype == "image_base64":
            out.append("[IMG]")
    return " ".join(out)

def clean_answer_text(answer_text):
    """
    Removes any leading labels like "A. ", "A. A. ", etc.
    E.g., "A. A. Take EBS snapshots..." becomes "Take EBS snapshots..."
    """
    # Remove patterns like "A. A. ", "B. B. ", etc.
    pattern = r'^([A-Z]\.\s+)+'
    cleaned_text = re.sub(pattern, '', answer_text)
    return cleaned_text

def clean_string(text):
    if not text:
        return ""
    text = text.strip()
    # Remove 'most voted' from anywhere to avoid revealing correctness
    text = re.sub(r"\bmost\s+voted\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s{2,}", " ", text)
    text = text.strip()
    # Remove non-ASCII characters
    text = text.encode("ascii", errors="ignore").decode()
    return text
