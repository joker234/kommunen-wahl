from bs4 import BeautifulSoup
from pprint import pprint
import requests
import sqlite3
import sys
import re

gemeinden = []

def get_available_chars():
    r = requests.get('http://www.onlinekommunen-bw.de/phpkommunen/index.php?action=alphabetisch&sub=stadt')
    content = re.sub(r'\\n', '', str(r.content))
    soup = BeautifulSoup(content, "lxml")
    char = soup.find('td', text='Wählen Sie einen Buchstaben:')
    chars = []
    print(char)
    while char.next_sibling != None:
        char = char.next_sibling
        chars.append(char.text)

    return chars

for char in get_available_chars():
    print("Getting Char {}".format(char))
    r = requests.get('http://www.onlinekommunen-bw.de/phpkommunen/index.php?action=alphabetisch&sub=stadt&sort={}'.format(char))
    content = re.sub(r'\\n', '', str(r.content))
    soup = BeautifulSoup(content, "lxml")
    gemeindetabelle = soup.find(
        'h3',
        text=re.compile(r'Wählen Sie eine Stadt oder Gemeinde aus der Liste aus')
    ).find_next('table')
    for entry in gemeindetabelle.children:
        if list(entry.children)[0].text == 'Name der Stadt / Gemeinde':
            continue
        gemid = re.search(';id=(\d+)"', str(list(entry.children)[5])).group(1)
        gemname = bytes(list(entry.children)[0].text, "utf-8").decode('unicode_escape')
        gemhomepage = requests.get('http://www.onlinekommunen-bw.de/phpkommunen/redirect.php?action=stadt&id={}'.format(gemid), allow_redirects=False).headers['Location']
        gemeinde = {
            'id': gemid,
            'name': gemname,
            'homepage': gemhomepage,
        }
        print(gemeinde)
        gemeinden.append(gemeinde)

# establishing sqlite3 connection and create table
conn = sqlite3.connect('gemeinden.sqlite')
c = conn.cursor()

c.execute('DROP TABLE IF EXISTS gemeinden')
c.execute('''CREATE TABLE gemeinden
        (id INTEGER PRIMARY KEY, name TEXT, homepage TEXT)''')

for gemeinde in gemeinden:
    c.execute(
        "INSERT INTO gemeinden VALUES ('{}', '{}', '{}')".format(
            gemeinde['id'],
            gemeinde['name'],
            gemeinde['homepage']
        )
    )

conn.commit()
conn.close()
