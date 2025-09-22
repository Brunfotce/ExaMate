import random
import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import sqlite3
import datetime


fail=0
conn = sqlite3.connect("RobberDB.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

cur.execute("""
CREATE TABLE IF NOT EXISTS visited_urls(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS escanned_url (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    dateCreated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    last_number INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

conn.commit()
success=0
def save_html_from_url(url, filename="output.html"):
    global success
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
        )
    }
    Num_prefix = 3
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        current_url= response.url
        title = soup.title.string.strip() if soup.title else "output"
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)  # remove invalid characters
        # Create folder if it doesn't exist
        os.makedirs("Robbed", exist_ok=True)

        # Save inside Robbed folder
        filename = os.path.join("Robbed", f"{safe_title}.html")
        
        #check if file meet the filter
        #if filt.lower() not in safe_title.lower():

        # Fix relative links (CSS, JS, images)
        for tag in soup.find_all(["a", "link", "script", "img"]):
            attr = "href" if tag.name in ["a", "link"] else "src"
            if tag.has_attr(attr):
                tag[attr] = urljoin(url, tag[attr])

        # Remove lines containing "popup"
        for popup_tag in soup.find_all(string=lambda text: "popup" in text.lower()):
            popup_tag.extract()
        
        GROUP_WORDS = 3
        words = safe_title.split()
        prefix = " ".join(words[:GROUP_WORDS]) if len(words) >= GROUP_WORDS else safe_title

        sub_folder= os.path.join("Robbed",prefix)
        os.makedirs(sub_folder, exist_ok=True)
        filename= os.path.join(sub_folder, f"{safe_title}.html")
        
        with open(filename, "w", encoding="utf-8") as file:
            file.write(str(soup))
        cur.execute("INSERT OR IGNORE INTO files (filename) VALUES (?)", (safe_title,))
        conn.commit()
        cur.execute("INSERT OR IGNORE INTO visited_urls (url) VALUES (?)", (current_url,))
        conn.commit()
        
        print(f"Legible HTML saved to {filename}")
        success=success+1
    except requests.exceptions.RequestException as e:
        print(f"-----An error has occured, verify logs for further details")
        now= datetime.datetime.now()
        with open("ErrorLogs.txt","a") as Log:
            Log.write(f"-----Error has occured at {now} , Description: {e} \n")

def escaneo(url):
    global fail
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
            )
        }
    try:
        #CONNECTION
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        #STORE DATA TO CARIABLE soup AND EXTRACTS TITLE TO VARIABLE safe_title
        soup = BeautifulSoup(response.text, "html.parser")
        current_url= response.url
        title = soup.title.string.strip() if soup.title else "output"
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)  # remove invalid characters

        #CHECKS IF IS ALREADY STORED
        cur.execute("SELECT 1 FROM escanned_url WHERE title = ?", (safe_title,))
        exists = cur.fetchone()
        if exists:
            print(f"File already recorded and stored, skipping...")
            fail=0
            return        
    
        #IF NOT STORED THEN SAVES
        cur.execute("INSERT OR IGNORE INTO escanned_url (title, url) VALUES (?, ?)", (safe_title, current_url))
        conn.commit()
        print(safe_title)
        print(f"Saved link and title to DB {current_url}")
        fail=0
        
    except requests.exceptions.RequestException as e:
        print(f"-----An error has occured, verify logs for further details")
        now= datetime.datetime.now()
        fail +=1
        with open("ErrorLogs.txt","a") as Log:
            Log.write(f"-----Error has occured at {now} , Description: {e} \n")

Urlvar="0"
Waiting= 0.00

def desi(des):
    cur.execute("SELECT last_number FROM progress ORDER BY id DESC LIMIT 1")
    bibi= cur.fetchone()
    if bibi:
        Urlvar = bibi[0]   
    else:
        Urlvar = 0
    Waiting= 0.00
    match des:
        case 1:
            conn = sqlite3.connect("RobberDB.db")
            while fail<99:
                Urlvar=str(Urlvar)
                url = f"https://www.examtopics.com/discussions/amazon/view/{Urlvar}-exam-aws-certified-cloud-practitioner-clf-c02-topic-1/"
                sleep= round(random.uniform(1,3),2)
                time.sleep(sleep)
                Waiting= Waiting + sleep
                print(f"It has passed: {sleep} seconds: Total time elapsed: {round(Waiting,2)} Id number: {Urlvar}")
                escaneo(url)
                Urlvar=int(Urlvar)+1
                cur.execute("DELETE FROM progress")  # keep only one row
                cur.execute("INSERT INTO progress (last_number) VALUES (?)", (Urlvar,))
                conn.commit()
            print("-----The execution ended")
            return "Program finished cprrectly"
        case 2:
            conn = sqlite3.connect("RobberDB.db")
            user_input= input("Enter serial code exam or keyword ").strip()
            print(f"filters gathered are: {user_input}")    
            

            cur.execute("SELECT url FROM escanned_url WHERE LOWER(title) LIKE" +"\'%"+user_input+"%\'")
            result= cur.fetchall()
            for (xd,) in result:
                save_html_from_url(xd)
                    
            return "Program Finished correctly"
            
        case _:
            return "no valid"


if __name__ == "__main__":
    des= int(input("What would you like to do? 1) Scann and save links in local BD 2) Download form links in BD: "))
    print(desi(des))
    
   

    '''
    print("hello")
conn = sqlite3.connect("example.db")

cur = conn.cursor()

cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    age INTEGER
                    )
""")
cur.execute("INSERT INTO users (name, age) VALUES (?, ?)", ("Alice", 25))
cur.execute("INSERT INTO users (name, age) VALUES (?, ?)", ("Bob", 30))
conn.commit()
rows= cur.fetchall()
for row in rows:
    print(row)
cur.execute("SELECT * FROM users")
tables = cur.fetchall()

for table_name in tables:
    cur.execute(f'DROP TABLE IF EXISTS {table_name[0]}')

conn.close()
    '''

    '''
    Waiting= 0.00
    user_input= input("Enter serial code exam or keywords (if more than one, separate them by commas: ")
    filt= [f.strip() for f in user_input.split(",") if f.strip()]
    print(f"filters gathered are: {filt}")
    for x in range(500):
        Urlvar=str(Urlvar)
        url = f"https://www.examtopics.com/discussions/amazon/view/{Urlvar}-exam-aws-certified-cloud-practitioner-clf-c02-topic-1/"
        sleep= round(random.uniform(2,4),2)
        time.sleep(sleep)
        Waiting= Waiting + sleep
        print(f"It has passed: {sleep} seconds: Total time elapsed: {round(Waiting,2)} Id number: {Urlvar}")
        save_html_from_url(url)
        Urlvar=int(Urlvar)-1
print(f"program finished and recolected a total of {success} html fetched")
    '''