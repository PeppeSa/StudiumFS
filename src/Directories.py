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

class DirectoriesManager():

    def get_departments(self, url, session, user_cookie): # Recupera il nome delle cartelle relative ai dipartimenti
        pageText = session.get(url, cookies=dict(dk_sid=user_cookie))
        list = bs4.BeautifulSoup(pageText.text, 'html.parser').find(class_='home_cats').find('ul').find_all('a')
        degreeCourses = []
        for x in list:
            if x.get('href').split('=')[-1] != '24CFU':
                degreeCourses.append(dict(name = x.text, cid = x.get('href').split('=')[-1]))
        return degreeCourses

    def get_degreeCourses(self, url, category, session, user_cookie): # Recupera il nome delle cartelle relative ai CdL
        pageText = session.get(url + 'index.php?category=' + str(category), cookies=dict(dk_sid=user_cookie))
        list = bs4.BeautifulSoup(pageText.text, 'html.parser').find(class_='home_cats').find('ul').find_all('a')
        degreeCourses = []
        for x in list:
            degreeCourses.append(dict(name = x.text, cid = x.get('href').split('=')[-1]))
        return degreeCourses

    def get_teachings(self, url, category, session, user_cookie): # Recupera nome e codice di una materia
        pageText = session.get(url + 'index.php?category=' + str(category), cookies=dict(dk_sid=user_cookie))
        list = bs4.BeautifulSoup(pageText.text, 'html.parser').find(class_='home_cats').find('ul').find_all('a')
        teachings = []
        for x in list:
            teachings.append(dict(name = x.text, cid = x.get('href').split('/')[-2].split('=')[-1]))
        return teachings

    def get_errors(self, url, category, session, user_cookie):
        print('\nC\'e\' qualquadra che non cosa...')
