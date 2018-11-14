import bs4
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

    def get_file(self, url, session):   # Recupera i dati di un singolo annuncio
        pageText = session.get(url)
        title = bs4.BeautifulSoup(pageText.text, 'html.parser').find(class_='announcement_title').string
        announcementBS4 = bs4.BeautifulSoup(pageText.text, 'html.parser').find(class_='announcement_content').contents
        announcement = ''
        for s in announcementBS4:
            announcement += s.encode('utf-8')
        parser = MyHTMLParser()
        parser.feed(announcement)
        return dict(title=title, text=parser.data)

    def get_files(self, url, auth, cidReq, session): # Recupera tutti gli annunci di una materia
        localUrl = 'main/announcements/'
        session.post(url + localUrl + 'announcements.php', data=auth)
        pageText = session.get(url + localUrl + 'announcements.php?cidReq=' + cidReq)
        list = bs4.BeautifulSoup(pageText.text, 'html.parser').find_all('a')
        lista_files = []
        for x in list:
            if(x.get('href') and x.get('title')):
                lista_files.append(self.get_file(url + localUrl + x.get('href'), session))
        return lista_files
	
    def get_departments(self, url, auth, session): # Recupera il nome delle cartelle relative ai dipartimenti
        pageText = session.get(url)
        list = bs4.BeautifulSoup(pageText.text, 'html.parser').find(class_='home_cats').find('ul').find_all('a')
        degreeCourses = []
        for x in list:
            if x.get('href').split('=')[-1] != '24CFU':
                degreeCourses.append(dict(name = x.text, cid = x.get('href').split('=')[-1]))
        return degreeCourses

    def get_degreeCourses(self, url, auth, category, session): # Recupera il nome delle cartelle relative ai CdL
        pageText = session.get(url + 'index.php?category=' + str(category))
        list = bs4.BeautifulSoup(pageText.text, 'html.parser').find(class_='home_cats').find('ul').find_all('a')
        degreeCourses = []
        for x in list:
            degreeCourses.append(dict(name = x.text, cid = x.get('href').split('=')[-1]))
        return degreeCourses

    def get_teachings(self, url, auth, category, session): # Recupera nome e codice di una materia
        pageText = session.get(url + 'index.php?category=' + str(category))
        list = bs4.BeautifulSoup(pageText.text, 'html.parser').find(class_='home_cats').find('ul').find_all('a')
        teachings = []
        for x in list:
            teachings.append(dict(name = x.text, cid = x.get('href').split('/')[-2].split('=')[-1]))
        return teachings

    def get_errors(self, url, auth, category, session):
        print('\nC\'e\' qualquadra che non cosa...')

if __name__ == '__main__':
    url = 'http://studium.unict.it/dokeos/2018/'
    auth = {
        'login': raw_input('Nome utente: '),
        'password': getpass('Password: ')
    }
