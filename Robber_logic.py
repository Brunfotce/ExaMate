import random
import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import sqlite3
import datetime
import threading

class RobberLogic:
    def __init__(self, db_path="RobberDB.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cur = self.conn.cursor()
        self._initialize_db()
        self.stop_event = threading.Event()

    def _initialize_db(self):
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS visited_urls(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS escanned_url (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            dateCreated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_number INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        self.conn.commit()

    def get_last_scan_id(self):
        self.cur.execute("SELECT last_number FROM progress ORDER BY id DESC LIMIT 1")
        result = self.cur.fetchone()
        return result[0] if result else 0

    def save_html_from_url(self, url, update_callback):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            current_url = response.url
            title = soup.title.string.strip() if soup.title else "output"
            safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)

            # --- Start of file I/O operations ---
            try:
                os.makedirs("Robbed", exist_ok=True)
                
                GROUP_WORDS = 3
                words = safe_title.split()
                prefix = " ".join(words[:GROUP_WORDS]) if len(words) >= GROUP_WORDS else safe_title
                sub_folder = os.path.join("Robbed", prefix)
                os.makedirs(sub_folder, exist_ok=True)
                filename = os.path.join(sub_folder, f"{safe_title}.html")

                for tag in soup.find_all(["a", "link", "script", "img"]):
                    attr = "href" if tag.name in ["a", "link"] else "src"
                    if tag.has_attr(attr):
                        tag[attr] = urljoin(url, tag[attr])

                for popup_tag in soup.find_all(string=lambda text: "popup" in text.lower()):
                    popup_tag.extract()

                with open(filename, "w", encoding="utf-8") as file:
                    file.write(str(soup))
                
                self.cur.execute("INSERT OR IGNORE INTO files (filename) VALUES (?)", (safe_title,))
                self.conn.commit()
                self.cur.execute("INSERT OR IGNORE INTO visited_urls (url) VALUES (?)", (current_url,))
                self.conn.commit()
                
                update_callback(f"Legible HTML saved to {filename}")
                return True
            except Exception as e:
                error_message = f"-----Error saving file for URL {url}: {e}"
                update_callback(error_message)
                now = datetime.datetime.now()
                with open("ErrorLogs.txt", "a") as Log:
                    Log.write(f"-----Error has occurred at {now}, Description: {error_message} \n")
                return False
            # --- End of file I/O operations ---

        except requests.exceptions.RequestException as e:
            update_callback(f"-----An error has occurred during request: {e}")
            now = datetime.datetime.now()
            with open("ErrorLogs.txt", "a") as Log:
                Log.write(f"-----Error has occurred at {now}, Description: {e} \n")
            return False

    def escaneo(self, url, update_callback):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            current_url = response.url
            title = soup.title.string.strip() if soup.title else "output"
            safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)

            self.cur.execute("SELECT 1 FROM escanned_url WHERE title = ?", (safe_title,))
            if self.cur.fetchone():
                update_callback(f"File already recorded and stored, skipping...")
                return False
        
            self.cur.execute("INSERT OR IGNORE INTO escanned_url (title, url) VALUES (?, ?)", (safe_title, current_url))
            self.conn.commit()
            update_callback(f"Saved link and title to DB: {safe_title} ({current_url})")
            return True
        except requests.exceptions.RequestException as e:
            update_callback(f"-----An error has occurred: {e}")
            now = datetime.datetime.now()
            with open("ErrorLogs.txt", "a") as Log:
                Log.write(f"-----Error has occurred at {now}, Description: {e} \n")
            return False

    def start_scanning(self, start_id, update_callback):
        self.stop_event.clear()
        fail_count = 0
        waiting_time = 0.0
        current_id = int(start_id)

        while not self.stop_event.is_set() and fail_count < 99:
            url = f"https://www.examtopics.com/discussions/amazon/view/{current_id}-exam-aws-certified-cloud-practitioner-clf-c02-topic-1/"
            sleep_duration = round(random.uniform(1, 3), 2)
            time.sleep(sleep_duration)
            waiting_time += sleep_duration
            
            update_callback(f"It has passed: {sleep_duration}s: Total time elapsed: {round(waiting_time, 2)}s Id number: {current_id}")
            
            if self.escaneo(url, update_callback):
                fail_count = 0
            else:
                fail_count += 1

            current_id += 1
            self.cur.execute("DELETE FROM progress")
            self.cur.execute("INSERT INTO progress (last_number) VALUES (?)", (current_id,))
            self.conn.commit()
        
        if self.stop_event.is_set():
            update_callback("-----Scanning stopped by user.")
        else:
            update_callback("-----The execution ended.")

    def start_downloading(self, keyword, update_callback):
        self.stop_event.clear()
        update_callback(f"Filters gathered are: {keyword}")
        
        self.cur.execute("SELECT url FROM escanned_url WHERE LOWER(title) LIKE ?", (f'%{keyword.lower()}%',))
        results = self.cur.fetchall()
        
        update_callback(f"Found {len(results)} URLs to download.")

        for (url,) in results:
            if self.stop_event.is_set():
                update_callback("-----Downloading stopped by user.")
                break
            self.save_html_from_url(url, update_callback)
        
        if not self.stop_event.is_set():
            update_callback("-----Program Finished correctly.")

    def stop_operation(self):
        self.stop_event.set()

    def close_connection(self):
        self.conn.close()
