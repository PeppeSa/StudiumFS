import bs4
import sys
import re

from HTMLParser import HTMLParser

reload(sys)
sys.setdefaultencoding('utf8')

class UsersManager():
    
    def get_user(self, url, session, user_cookie):   # Recupera i dati di un singolo annuncio
        localUrl = url + 'main/social/profile.php'
        pageText = session.get(localUrl, cookies=dict(dk_sid=user_cookie))
        userBS4 = bs4.BeautifulSoup(pageText.text, 'html.parser').find(class_='social-box-left')
        userBS4.append(bs4.BeautifulSoup(pageText.text, 'html.parser').find(class_='social-box-container2'))
        return userBS4.encode('ascii')

    #def update_user(self, url, category, session, content, id, title, auth):
    #    localUrl = 'main/announcements/announcements.php'
    #    form = {
    #        'login': auth[0],
    #        'password': auth[1],
    #        'title': title,
    #        'content': content,
    #        'submit_announcement': '',
    #        '_qf__announcement_form': '',
    #        'announcement_id': id
    #    }
    #    params = {
    #        'cidReq': category,
    #        'action': 'edit',
    #        'id': id
    #    }
    #    headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
    #    return session.post(url + localUrl, params=params, data=form, headers=headers)
        