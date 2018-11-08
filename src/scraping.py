import bs4
import requests
import sys
from HTMLParser import HTMLParser

reload(sys)
sys.setdefaultencoding('utf8')

class MyHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.data = ''

    def handle_data(self, data):
        self.data += data

class FileManager():
    def get_file(self, url, session):   # Recupera un singolo annuncio
        pageText = session.get(url)
        title = bs4.BeautifulSoup(pageText.text, 'html.parser').find(class_='announcement_title').string
        announcementBS4 = bs4.BeautifulSoup(pageText.text, 'html.parser').find(class_='announcement_content').contents
        announcement = ''
        for s in announcementBS4:
            announcement += s.encode('utf-8')
        parser = MyHTMLParser()
        parser.feed(announcement)
        return dict(title=title, text=parser.data)

    def get_files(self, url, auth, cidReq): # Recupera tutti gli annunci di una materia
        with requests.Session() as session:
            session.post(url + 'announcements.php', data=auth)
            pageText = session.get(url + 'announcements.php?cidReq='+cidReq)
            list = bs4.BeautifulSoup(pageText.text, 'html.parser').find_all('a')
            lista_files = []
            for x in list:
                if(x.get('href') and x.get('title')):
                    lista_files.append(self.get_file(url + x.get('href'), session))
            return lista_files

    def get_teachings(self): # Codice statico temporaneo
        combo = [{'name': 'Sistemi Operativi', 'cid': '9114'}, {'name': 'Elementi di Analisi Matematica M-Z', 'cid': '9111'}]
        return combo

if __name__ == '__main__':
    url = 'http://studium.unict.it/dokeos/2018/main/'
    auth = {
        'login': raw_input('Nome utente: '),
        'password': getpass('Password: ')
    }
