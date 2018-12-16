from __future__ import print_function, absolute_import, division

import logging
from getpass import getpass

import requests
from collections import defaultdict
from errno import ENOENT
from stat import S_IFDIR, S_IFLNK, S_IFREG
from sys import argv, exit
from time import time
import sys

reload(sys)
sys.setdefaultencoding('utf8')

from fuse import FUSE, FuseOSError, LoggingMixIn    #La classe Operations imposta in automatico il VFS in Read-Only, quindi e' stata rimossa

from src.Announcements import AnnouncementsManager
from src.Descriptions import DescriptionsManager
from src.Directories import DirectoriesManager
from src.Documents import DocumentsManager
from src.Terms import TermsManager
from src.Users import UsersManager

if not hasattr(__builtins__, 'bytes'):
    bytes = str

auth = (raw_input('Nome utente: '), getpass('Password: '))
url = 'http://studium.unict.it/dokeos/2018/'
switch = {
    2: 'degreeCourse',
    3: 'teaching',
    4: 'categorie',
    5: 'file'
}
switchMethod = {
    'Annunci': 'announcement',
    'Documenti': 'document',
    'Glossario': 'term',
    'Collegamenti': 'link',
    'Descrizione': 'description'
}
switchClass = {
    'announcement': 'Announcements',
    'document': 'Documents',
    'term': 'Terms',
    'link': 'Links',
    'description': 'Descriptions'
}
session = requests.Session()

class Memory(LoggingMixIn):
    
    def __init__(self):
        self.user_cookie = session.post(url + 'index.php', data={'login': auth[0], 'password': auth[1]}).cookies['dk_sid']
        self.departments = DirectoriesManager().get_departments(url, session, self.user_cookie)
        self.files = {}
        self.data = defaultdict(bytes)
        self.fd = 0
        self.cids = {}
        self.ids = {}
        now = time()
        self.files['/'] = dict(st_mode=(S_IFDIR | 0o755), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=3)
        user = UsersManager().get_user(url, session, self.user_cookie)
        self.files['/Utente.html'] = dict(st_mode=(S_IFREG | 0o444), st_nlink=1, st_size=len(user), st_ctime=now, st_mtime=now, st_atime=now)
        self.data['/Utente.html'] = user
        # self.files['/Utente'] = dict(st_mode=(S_IFREG | 0o444), st_nlink=1, st_size=len(user), st_ctime=now, st_mtime=now, st_atime=now)
        # self.data['/Utente'] = user
        for department in self.departments:
            self.files['/' + department['name']] = dict(st_mode=(S_IFDIR | 0o755), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=3)
            self.cids['/' + department['name']] = department['cid']

    def chmod(self, path, mode):
        self.files[path]['st_mode'] &= 0o770000
        self.files[path]['st_mode'] |= mode
        return 0
    
    def create(self, path, mode):
        title = path.split('/')[-1]
        with requests.Session() as session:
            now = time()
            if len(path.split('/')[-1].split('.')) == 1:
                if AnnouncementsManager().create_announcement(url, '9114', session, title, self.user_cookie).status_code == 200:
                    self.files[path] = dict(st_mode=(S_IFREG | mode), st_nlink=1, st_size=len(''), st_ctime=now, st_mtime=now, st_atime=now)
                    print('\nAnnuncio pubblicato con successo!')
                    self.fd += 1

                    parent_path = ''
                    for dir in path.split('/')[1:-1]:
                        parent_path += '/' + dir

                    result = AnnouncementsManager().get_announcements(url, self.cids[parent_path], session, self.user_cookie)
                    for ris in result:
                        myPath = parent_path + '/' + ris['title']
                        self.files[myPath] = dict(st_mode=(S_IFREG | 0o444), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=1, st_size=len(ris['text']))
                        self.data[myPath] = ris['text']
                        self.ids[myPath] = ris['ann_id']

                elif title.split('.')[0] == '':    #permette al vfs di creare file temporanei in modo trasparente rispetto al server
                    print('\nSto creando un file temporaneo')
                    self.files[path] = dict(st_mode=(S_IFREG | mode), st_nlink=1, st_ctime=now, st_mtime=now, st_atime=now)
                else:
                    print('\nErrore avvenuto durante la pubblicazione dell\'annuncio!')
            else:
                print('\nSto creando un file che non deve essere inviato al server')
        return self.fd

    def getattr(self, path, fh=None):
        if path not in self.files:
            raise FuseOSError(ENOENT)
        return self.files[path]

    def read(self, path, size, offset, fh):
        return self.data[path][offset:offset + size]

    def readdir(self, path, fh):
        list = ['.', '..']
        now = time()
        if path != '/':
            if path + '/' not in str(self.files):
                switchIndex = len(path.split('/'))
                func_name = switch.get(switchIndex, 'error')

                if func_name is 'categorie':
                    self.files[path + '/Annunci'] = dict(st_mode=(S_IFDIR | 0o755), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=3)
                    self.cids[path + '/Annunci'] = self.cids[path]
                    self.files[path + '/Collegamenti'] = dict(st_mode=(S_IFDIR | 0o755), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=3)
                    self.cids[path + '/Collegamenti'] = self.cids[path]
                    self.files[path + '/Descrizione'] = dict(st_mode=(S_IFDIR | 0o755), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=3)
                    self.cids[path + '/Descrizione'] = self.cids[path]
                    self.files[path + '/Documenti'] = dict(st_mode=(S_IFDIR | 0o755), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=3)
                    self.cids[path + '/Documenti'] = self.cids[path]
                    self.files[path + '/Glossario'] = dict(st_mode=(S_IFDIR | 0o755), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=3)
                    self.cids[path + '/Glossario'] = self.cids[path]

                else:
                    if func_name is 'file':
                        func_name = path.split('/')[4]
                        func_name = switchMethod.get(func_name, 'error')
                    class_name = switchClass.get(func_name, 'Directories')

                    if class_name == 'Directories':
                        result = getattr(DirectoriesManager(), 'get_' + func_name + 's')(url, self.cids[path], session, self.user_cookie)
                    elif class_name == 'Announcements':
                        result = getattr(AnnouncementsManager(), 'get_' + func_name + 's')(url, self.cids[path], session, self.user_cookie)
                    elif class_name == 'Links':
                        result = getattr(LinksManager(), 'get_' + func_name + 's')(url, self.cids[path], session, self.user_cookie)
                    elif class_name == 'Descriptions':
                        result = getattr(DescriptionsManager(), 'get_' + func_name + 's')(url, self.cids[path], session, self.user_cookie)
                    elif class_name == 'Documents':
                        result = getattr(DocumentsManager(), 'get_' + func_name + 's')(url, self.cids[path], session, self.user_cookie)
                    elif class_name == 'Terms':
                        result = getattr(TermsManager(), 'get_' + func_name + 's')(url, self.cids[path], session, self.user_cookie)

                    c = 1
                    for ris in result:
                        if func_name is 'announcement':
                            myPath = path + '/' + ris['title']
                            if myPath + '.html' in self.files:
                            # if myPath in self.files:
                                myPath += '(' + str(c) + ')'
                                c += 1
                            myPath += '.html'
                            self.files[myPath] = dict(st_mode=(S_IFREG | 0o444), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=1, st_size=len(ris['text']))
                            self.data[myPath] = ris['text']
                            self.ids[myPath] = ris['ann_id']

                        elif func_name is 'document':
                            myPath = path + '/' + ris['title']
                            if myPath in self.files:
                                myPath += '(' + str(c) + ')'
                                c += 1
                            self.files[myPath] = dict(st_mode=(S_IFREG | 0o444), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=1, st_size=len(ris['text']))
                            self.data[myPath] = ris['text']

                        elif func_name is 'term':
                            myPath = path + '/' + ris['title']
                            if myPath in self.files:
                                myPath += '(' + str(c) + ')'
                                c += 1
                            self.files[myPath] = dict(st_mode=(S_IFREG | 0o444), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=1, st_size=len(ris['text']))
                            self.data[myPath] = ris['text']
                            self.ids[myPath] = ris['ann_id']

                        elif func_name is 'link':
                            myPath = path + '/' + ris['title']
                            if myPath in self.files:
                                myPath += '(' + str(c) + ')'
                                c += 1
                            self.files[myPath] = dict(st_mode=(S_IFREG | 0o444), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=1, st_size=len(ris['text']))
                            self.data[myPath] = ris['text']
                            self.ids[myPath] = ris['ann_id']

                        elif func_name is 'description':
                            myPath = path + '/' + ris['title']
                            if myPath + '.html' in self.files:
                            # if myPath in self.files:
                                myPath += '(' + str(c) + ')'
                                c += 1
                            myPath += '.html'
                            self.files[myPath] = dict(st_mode=(S_IFREG | 0o444), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=1, st_size=len(ris['text']))
                            self.data[myPath] = ris['text']
                            print('\npercorso:\n' + str(myPath) + '\ncontenuto:\n' + str(self.data[myPath]))

                        else:
                            myPath = path + '/' + ris['name']
                            if myPath in self.files:
                                myPath += '(' + str(c) + ')'
                                c += 1
                            self.files[myPath] = dict(st_mode=(S_IFDIR | 0o755), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=3)
                            self.cids[myPath] = ris['cid']

            for filePath in self.files:
                if str(path) in str(filePath):
                    fileName = filePath.split('/')[-1]
                    if fileName != '':
                        list += [fileName]
        else:
            list += ['Utente.html']
            # list += ['Utente']
            for department in self.departments:
                list += [department['name']]
        return list
    
    def rename(self, old, new):
        with requests.Session() as session:
            r = AnnouncementsManager().update_announcement(url, '9114', session, self.data[old], self.ids[old], new.split('/')[-1], self.user_cookie)
            if r.status_code == 200:
                self.files[new] = self.files.pop(old)
                self.data[new] = self.data.pop(old)
                self.ids[new] = self.ids.pop(old)

    def truncate(self, path, length, fh=None):
        if length != 0:
            with requests.Session() as session:
                newData = self.data[path][:length]
                if AnnouncementsManager().update_announcement(url, '9114', session, newData, self.ids[path], path.split('/')[-1], self.user_cookie).status_code != 200:
                    print('Non ho potuto modificare l\'annuncio!')
                else:
                    self.data[path] = newData
                    self.files[path]['st_size'] = length
     
    def unlink(self, path):
        if path.split('/')[-1].split('.')[0] != '':    #permette al vfs di cancellare file temporanei in modo trasparente rispetto al server
            r = AnnouncementsManager().delete_announcement(url, '9114', session, self.ids[path])
            if r.status_code == 200:
                self.files.pop(path)
                self.ids.pop(path)
                self.data.pop(path)
                print('\nAnnuncio rimosso')
            else:
                print('Non ho potuto rimuovere l\'annuncio!')
        else:
            print('\nSto eliminando un file temporaneo')
            self.files.pop(path)
   
    def write(self, path, data, offset, fh):
        newData = self.data[path][:offset] + data
        if len(path.split('/')[-1].split('.')) == 1:
            r = AnnouncementsManager().update_announcement(url, '9114', session, newData, self.ids[path], path.split('/')[-1], self.user_cookie)
            if r.status_code == 200:
                self.data[path] = newData
                self.files[path]['st_size'] = len(self.data[path])
                return len(data)
            else:
                print('Non ho potuto modificare l\'annuncio!')
        else:
            print('\nSto modificando un file che non deve essere inviato al server')
        
if __name__ == '__main__':
    if len(argv) != 2:
        print('usage: %s <mountpoint>' % argv[0])
        exit(1)

    logging.basicConfig(level=logging.DEBUG)
    fuse = FUSE(Memory(), argv[1], foreground=True)
