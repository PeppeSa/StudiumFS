import bs4
import sys
from HTMLParser import HTMLParser

reload(sys)
sys.setdefaultencoding('utf8')

class DescriptionsManager():

    # def create_announcement(self, url, category, session, title, user_cookie):
    #     localUrl = 'main/announcements/announcements.php'
    #     form = {
    #         'title': title,
    #         'content': '',
    #         'submit_announcement': '',
    #         '_qf__announcement_form': ''
    #     }
    #     params = {
    #         'cidReq': category,
    #         'action': 'add'
    #     }
    #     headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
    #     return session.post(
    #         url + localUrl,
    #         params=params,
    #         data=form,
    #         headers=headers,
    #         cookies=dict(dk_sid=user_cookie)
    #     )
        
    # def delete_announcement(self, url, category, session, id, user_cookie):
    #     localUrl = 'main/announcements/announcements.php'
    #     params = {
    #         'cidReq': category,
    #         'action': 'delete',
    #         'id': id
    #     }
    #     return session.get(url + localUrl, params=params, cookies=dict(dk_sid=user_cookie))
    
    def get_descriptions(self, url, cidReq, session, user_cookie): # Recupera tutti gli annunci di una materia
        localUrl = 'main/course_description/'
        pageText = session.get(url + localUrl + '?cidReq=' + cidReq, cookies=dict(dk_sid=user_cookie))
        list = bs4.BeautifulSoup(pageText.text, 'html.parser').find_all('div', class_='section_white')
        lista_files = []
        for x in list:
            if x.find('div', class_='sectiontitle') and x.find('div', class_='sectioncontent'):
                title = x.find('div', class_='sectiontitle').string
                content = x.find('div', class_='sectioncontent').contents[0].encode('ascii')
                lista_files.append(dict(title=title, text=content))
        return lista_files
	
    # def update_announcement(self, url, category, session, content, id, title, user_cookie):
    #     localUrl = 'main/announcements/announcements.php'
    #     form = {
    #         'title': title,
    #         'content': content,
    #         'submit_announcement': '',
    #         '_qf__announcement_form': '',
    #         'announcement_id': id
    #     }
    #     params = {
    #         'cidReq': category,
    #         'action': 'edit',
    #         'id': id
    #     }
    #     headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
    #     return session.post(url + localUrl, params=params, data=form, headers=headers, cookies=dict(dk_sid=user_cookie))
        