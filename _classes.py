from bs4 import BeautifulSoup as bs
import os
import re
import urllib.parse

class AnswerPart:
    """
    Represents a portion of an answer: either text or an image path.
    e.g. ("text", "some text..."), ("image", "/path/to/image.jpg")
    """
    def __init__(self, ptype, content):
        self.ptype = ptype
        self.content = content

class Card:
    """ 
        Represents one question, multi-choice answers, correct answers,
        question text, question number, plus question parts (text/image).
        Each answer is a list of AnswerPart too, so some answers may have images.
    """
    def __init__(self, question: str, answers: list, correct_answer: list, question_number: str,
                 question_parts=None):
        self.question = question
        self.answers = answers            # This will be a list of lists (answer-part lists), explained below
        self.correct_answer = correct_answer
        self.question_number = question_number
        # question_parts is a list of (ptype, content) for the question text area
        self.question_parts = question_parts if question_parts else []

    def print_card(self):
        print("=" * 30)
        print(f"Question {self.question_number}")
        print("Text:", self.question)
        print("Correct answers:", self.correct_answer)
        print("Question Parts:")
        for qp in self.question_parts:
            print("   ", qp.ptype, qp.content)

        print("Answers:")
        for i, ans_parts in enumerate(self.answers):
            label = chr(ord("A") + i)
            print(f"{label}:")
            for ap in ans_parts:
                print("  -", ap.ptype, ap.content)


class CardList:
    """ Loads Card objects from .html or .htm files in a directory. """
    def __init__(self, resources_dir) -> None:
        self.resources_dir = resources_dir
        self.__page_soups = self.__init_soups(self.__get_html_files(resources_dir))
        self.cards_list = []

        for soup in self.__page_soups:
            new_cards = self.__parse_cards_from_soup(soup)
            self.cards_list.extend(new_cards)

    def __get_html_files(self, folder):
        """Return a list of .html or .htm files in 'folder'."""
        result = []
        for file in os.listdir(folder):
            path = os.path.join(folder, file)
            if os.path.isfile(path) and file.lower().endswith((".html", ".htm")):
                result.append(path)
        return result

    def __init_soups(self, html_files):
        soups = []
        for f in html_files:
            with open(f, "r", encoding="utf-8") as fh:
                soup = bs(fh.read(), "html.parser")
                soups.append(soup)
        return soups

    def __parse_cards_from_soup(self, soup):
        card_divs = soup.find_all("div", attrs={"class": "card exam-question-card"})
        cards = []
        for div in card_divs:
            q_parts = self.__parse_question_parts(div)
            question_text = self.__combine_text(q_parts)

            ans = self.__parse_answers(div)
            correct = self.__parse_correct_answers(div)
            qnum = self.__parse_question_number(div)

            card_obj = Card(question_text, ans, correct, qnum, q_parts)
            cards.append(card_obj)
        return cards

    def __parse_question_parts(self, card_div):
        """ 
        For the main question text <p class="card-text"> parse text & <img> 
        Return a list of AnswerPart objects: e.g. [AnswerPart("text","..."), AnswerPart("image","...")]
        """
        results = []
        p_tag = card_div.find("p", attrs={"class": "card-text"})
        if not p_tag:
            return results  # no question text at all

        for child in p_tag.children:
            if hasattr(child, "name") and child.name == "img":
                # It's an <img>
                src = child.get("src", "")
                decoded = urllib.parse.unquote(src)
                img_path = os.path.join(self.resources_dir, decoded)
                results.append(AnswerPart("image", img_path))
            else:
                # It's text or something else
                txt = child.string if child.string else child.get_text(separator=" ")
                txt = self.__clean_string(txt)
                if txt:
                    results.append(AnswerPart("text", txt))
        return results

    def __combine_text(self, question_parts):
        """ Combine text parts for a simpler 'question' string. """
        texts = [qp.content for qp in question_parts if qp.ptype == "text"]
        return " ".join(texts)

    def __parse_answers(self, card_div):
        """
        Each answer is an <li class="multi-choice-item">.
        We parse children in the li: text + <img> if any.
        Return a list of answer-part-lists, e.g. [ [AnswerPart("text","stuff"), ...], [AnswerPart("text","more"), AnswerPart("image","...")] ]
        """
        results = []
        li_items = card_div.find_all("li", attrs={"class": "multi-choice-item"})
        for li_tag in li_items:
            answer_parts = self.__parse_answer_parts(li_tag)
            results.append(answer_parts)
        return results

    def __parse_answer_parts(self, li_tag):
        """
        Parse text + images inside one <li> to produce a list of AnswerPart.
        """
        subresults = []
        for child in li_tag.children:
            if hasattr(child, "name") and child.name == "img":
                # image in answer
                src = child.get("src", "")
                decoded = urllib.parse.unquote(src)
                img_path = os.path.join(self.resources_dir, decoded)
                subresults.append(AnswerPart("image", img_path))
            else:
                # text
                t = child.string if child.string else child.get_text(separator=" ")
                t = self.__clean_string(t)
                if t:
                    subresults.append(AnswerPart("text", t))
        return subresults

    def __parse_correct_answers(self, card_div):
        """
        Return a list of letters, ignoring "most voted" so we don't reveal the correct answer.
        """
        cabody = card_div.find("p", attrs={"class": "card-text question-answer bg-light white-text"})
        if not cabody:
            return []
        comm = cabody.find("div", attrs={"class": "vote-bar progress-bar bg-primary"})
        if comm:
            raw = self.__clean_string(comm.get_text())
            # e.g. "AC 94%" -> we only want "AC"
            correct_str = raw.split()[0] if raw else ""
        else:
            span = cabody.find("span", attrs={"class": "correct-answer"})
            if not span:
                return []
            correct_str = self.__clean_string(span.get_text())
        # Now we parse it
        possible = re.split(r"[,\s]+", correct_str)
        possible = [x.strip().upper() for x in possible if x.strip()]
        if len(possible) == 1:
            # e.g. "AC" => ["A","C"]
            if re.match(r"^[A-Z]{2,}$", possible[0]):
                possible = list(possible[0])
        return possible

    def __parse_question_number(self, card_div):
        header = card_div.find("div", attrs={"class": "card-header text-white bg-primary"})
        if not header:
            return "0"
        raw = header.get_text(strip=True)
        # e.g. "Question #29..."
        # We'll just attempt to parse the second word
        parts = raw.split()
        if len(parts) >= 2:
            return parts[1].replace("#","")
        return raw

    def __clean_string(self, text):
        if not text:
            return ""
        text = text.strip()
        # remove 'most voted' from anywhere to avoid revealing correctness
        text = re.sub(r"\bmost\s+voted\b", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s{2,}", " ", text)
        text = text.strip()
        # remove weird ascii
        text = text.encode("ascii", errors="ignore").decode()
        return text


    def get_cards(self):
        return self.cards_list
