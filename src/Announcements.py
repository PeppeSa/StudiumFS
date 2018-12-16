import bs4
import sys
from HTMLParser import HTMLParser

reload(sys)
sys.setdefaultencoding('utf8')

class AnnouncementsManager():

    def create_announcement(self, url, category, session, title, user_cookie):
        localUrl = 'main/announcements/announcements.php'
        form = {
            'title': title,
            'content': '',
            'submit_announcement': '',
            '_qf__announcement_form': ''
        }
        params = {
            'cidReq': category,
            'action': 'add'
        }
        headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
        return session.post(
            url + localUrl,
            params=params,
            data=form,
            headers=headers,
            cookies=dict(dk_sid=user_cookie)
        )
        
    def delete_announcement(self, url, category, session, id, user_cookie):
        localUrl = 'main/announcements/announcements.php'
        params = {
            'cidReq': category,
            'action': 'delete',
            'id': id
        }
        return session.get(url + localUrl, params=params, cookies=dict(dk_sid=user_cookie))
    
    def get_announcement(self, url, session, user_cookie):   # Recupera i dati di un singolo annuncio
        pageText = session.get(url, cookies=dict(dk_sid=user_cookie))
        title = bs4.BeautifulSoup(pageText.text, 'html.parser').find(class_='announcement_title').string
        announcementBS4 = bs4.BeautifulSoup(pageText.text, 'html.parser').find(class_='announcement_content')
        # announcement = ''
        # for s in announcementBS4:
        #     announcement += s.encode('utf-8')
        return dict(title=title, text=announcementBS4.encode('ascii'), ann_id=url.split('=')[-1])

    def get_announcements(self, url, cidReq, session, user_cookie): # Recupera tutti gli annunci di una materia
        localUrl = 'main/announcements/'
        pageText = session.get(url + localUrl + 'announcements.php?cidReq=' + cidReq, cookies=dict(dk_sid=user_cookie))
        list = bs4.BeautifulSoup(pageText.text, 'html.parser').find_all('a')
        lista_files = []
        for x in list:
            if(x.get('href') and x.get('title')):
                lista_files.append(self.get_announcement(url + localUrl + x.get('href'), session, user_cookie))
        return lista_files
	
    def update_announcement(self, url, category, session, content, id, title, user_cookie):
        localUrl = 'main/announcements/announcements.php'
        form = {
            'title': title,
            'content': content,
            'submit_announcement': '',
            '_qf__announcement_form': '',
            'announcement_id': id
        }
        params = {
            'cidReq': category,
            'action': 'edit',
            'id': id
        }
        headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
        return session.post(url + localUrl, params=params, data=form, headers=headers, cookies=dict(dk_sid=user_cookie))
        