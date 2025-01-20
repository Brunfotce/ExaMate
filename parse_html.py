# parse_html.py

import os
import re
import base64
from bs4 import BeautifulSoup
import urllib.parse
import json
from utils import clean_answer_text, clean_string  # Importing helper functions

def parse_html_to_json(input_html_folder, output_json_path):
    """
    Parse .html / .htm files in input_html_folder,
    build an 'exam' structure, and save as .json with base64-encoded images.
    Each question includes question text, images, answers, and correct answers.
    """
    # Collect 'questions' as a list
    questions = []
    # Find all .html or .htm files
    html_files = [f for f in os.listdir(input_html_folder) if f.lower().endswith((".html", ".htm"))]
    
    for file in html_files:
        fullpath = os.path.join(input_html_folder, file)
        with open(fullpath, "r", encoding="utf-8") as fh:
            soup = BeautifulSoup(fh.read(), "html.parser")
            card_divs = soup.find_all("div", attrs={"class": "card exam-question-card"})
            
            for div in card_divs:
                # Parse question number
                qnum = parse_question_number(div)
                # Parse question text + images
                q_parts = parse_question_parts(div, input_html_folder)
                # Parse answers
                ans_list = parse_answers(div, input_html_folder)
                # Parse correct answers
                corr = parse_correct_answers(div)
                # Build question dict
                question_obj = {
                    "question_number": qnum if qnum else "0",
                    "question_parts": encode_parts_to_base64(q_parts),
                    "answers": [encode_parts_to_base64(a) for a in ans_list],
                    "correct_answers": corr
                }
                questions.append(question_obj)

    # Build the final exam structure
    exam_data = {
        "title": "ParsedExam",
        "questions": questions
    }
    # Write to .json
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(exam_data, f, indent=2)
    
    print(f"Parsing completed. JSON saved to {output_json_path}")

def parse_question_number(card_div):
    header = card_div.find("div", attrs={"class": "card-header text-white bg-primary"})
    if not header:
        return "0"
    raw = header.get_text(strip=True)
    parts = raw.split()
    if len(parts) >= 2:
        return parts[1].replace("#", "")
    return raw

def parse_question_parts(card_div, base_folder):
    """ 
    For the main question text <p class="card-text"> parse text & <img> 
    Return a list of tuples: e.g. [("text","some text..."), ("image","...")]
    """
    results = []
    p_tag = card_div.find("p", attrs={"class": "card-text"})
    if not p_tag:
        return results  # No question text at all

    for child in p_tag.children:
        if hasattr(child, "name") and child.name == "img":
            # It's an <img>
            src = child.get("src", "")
            decoded = urllib.parse.unquote(src)
            img_path = os.path.join(base_folder, decoded)
            results.append(("image", img_path))
        else:
            # It's text or something else
            txt = child.string if child.string else child.get_text(separator=" ")
            txt = clean_string(txt)
            if txt:
                # Note: We do not clean here as these are question parts, not answers
                results.append(("text", txt))
    return results

def combine_text(parts):
    """ Combine text parts for a simpler 'question' string. """
    texts = [p[1] for p in parts if p[0] == "text"]
    return " ".join(texts)

def parse_answers(card_div, base_folder):
    """
    Each answer is an <li class="multi-choice-item">.
    We parse children in the li: text + <img> if any.
    Return a list of answer-part-lists, e.g. [ [("text","stuff"), ...], [("text","more"), ("image","...")] ]
    """
    results = []
    li_items = card_div.find_all("li", attrs={"class": "multi-choice-item"})
    for li_tag in li_items:
        answer_parts = parse_answer_parts(li_tag, base_folder)
        results.append(answer_parts)
    return results

def parse_answer_parts(li_tag, base_folder):
    """
    Parse text + images inside one <li> to produce a list of tuples.
    Applies cleaning to remove redundant labels (e.g., "A. A. Take..." becomes "Take...")
    """
    subresults = []
    full_text = ''
    
    for child in li_tag.children:
        if hasattr(child, "name") and child.name == "img":
            # Image in answer
            src = child.get("src", "")
            decoded = urllib.parse.unquote(src)
            img_path = os.path.join(base_folder, decoded)
            subresults.append(("image", img_path))
        else:
            # Text
            t = child.string if child.string else child.get_text(separator=" ")
            t = clean_string(t)
            if t:
                full_text += t + ' '

    if full_text:
        # Clean the combined text to remove redundant labels
        cleaned_text = clean_answer_text(full_text.strip())
        subresults.insert(0, ("text", cleaned_text))  # Insert as the first text part

    return subresults

def parse_correct_answers(card_div):
    """
    Return a list of letters for correct answers based on 'correct' class in <li>.
    """
    correct_lis = card_div.find_all("li", attrs={"class": re.compile(r"multi-choice-item.*correct")})
    correct_letters = []
    print(f"Found {len(correct_lis)} correct answer(s).")
    for li in correct_lis:
        text = li.get_text(strip=True)
        print(f"Processing correct answer text: '{text}'")
        # Extract all letters before dots at the start
        # e.g., "A. A. Create..." should extract "A"
        match = re.match(r'^([A-Z])\.', text)
        if match:
            letter = match.group(1)
            print(f"Extracted correct answer: '{letter}'")
            correct_letters.append(letter)
        else:
            print(f"Warning: Unable to extract correct answer from text: '{text}'")
    if not correct_letters:
        print("Warning: No correct answers found for a question.")
    return correct_letters

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

def encode_parts_to_base64(parts):
    """
    Convert e.g. ("image", "/some/path.jpg") -> ("image_base64", <b64string>)
    or ("text","some text") -> ("text","some text")
    """
    encoded = []
    for (ptype, content) in parts:
        if ptype == "image":
            if os.path.exists(content):
                try:
                    with open(content, "rb") as imgf:
                        bdata = base64.b64encode(imgf.read()).decode("utf-8")
                    encoded.append(("image_base64", bdata))
                except Exception as e:
                    # Error reading file
                    print(f"Error encoding image {content}: {e}")
                    encoded.append(("image_base64", "ERROR"))
            else:
                print(f"Image not found: {content}")
                encoded.append(("image_base64", "NOT_FOUND"))
        else:
            encoded.append((ptype, content))
    return encoded

if __name__ == "__main__":
    # Example usage:
    input_folder = "../res/AWS Developer"  # Path to your actual HTML files folder
    output_folder = "exams"                # Exams folder
    # Ensure output_folder exists
    os.makedirs(output_folder, exist_ok=True)
    # Name the JSON after the input folder
    folder_name = os.path.basename(os.path.normpath(input_folder))
    output_json = os.path.join(output_folder, f"{folder_name}.json")
    parse_html_to_json(input_folder, output_json)
