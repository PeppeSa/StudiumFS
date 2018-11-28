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

from src.scraping import FileManager

if not hasattr(__builtins__, 'bytes'):
    bytes = str

auth = (raw_input('Nome utente: '), getpass('Password: '))
url = 'http://studium.unict.it/dokeos/2018/'
switch = {
    2: 'degreeCourse',
    3: 'teaching',
    4: 'announcement'
}

class Memory(LoggingMixIn):
    
    def __init__(self):
        with requests.Session() as session:
            session.post(url, auth=auth)
            self.departments = FileManager().get_departments(url, auth, session)
            self.files = {}
            self.data = defaultdict(bytes)
            self.fd = 0
            self.cids = {}
            self.ann_ids = {}
            now = time()
            self.files['/'] = dict(st_mode=(S_IFDIR | 0o755), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=3)
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
                if FileManager().create_announcement(url, '9114', session, title, auth).status_code == 200:
                    self.files[path] = dict(st_mode=(S_IFREG | mode), st_nlink=1, st_size=len(''), st_ctime=now, st_mtime=now, st_atime=now)
                    print('\nAnnuncio pubblicato con successo!')
                    self.fd += 1

                    parent_path = ''
                    for dir in path.split('/')[1:-1]:
                        parent_path += '/' + dir

                    result = FileManager().get_announcements(url, auth, self.cids[parent_path], session)
                    for ris in result:
                        myPath = parent_path + '/' + ris['title']
                        self.files[myPath] = dict(st_mode=(S_IFREG | 0o444), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=1, st_size=len(ris['text']))
                        self.data[myPath] = ris['text']
                        self.ann_ids[myPath] = ris['ann_id']

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

    def open(self, path, flags):
        print('\nopen\npath: ' + str(path) + '\nflags: ' + str(flags))
        self.fd += 1
        return self.fd

    def read(self, path, size, offset, fh):
        return self.data[path][offset:offset + size]

    def readdir(self, path, fh):
        list = ['.', '..']
        now = time()
        if path != '/':
            if path + '/' not in str(self.files):
                with requests.Session() as session:
                    session.post(url, auth=auth)
                    switchIndex = len(path.split('/'))
                    func_name = switch.get(switchIndex, 'error')
                    result = getattr(FileManager(), 'get_' + func_name + 's')(url, auth, self.cids[path], session)
                    c = 1
                    for ris in result:
                        if func_name is 'announcement':
                            myPath = path + '/' + ris['title']
                            if myPath in self.files:
                                myPath += '(' + str(c) + ')'
                                c += 1
                            self.files[myPath] = dict(st_mode=(S_IFREG | 0o444), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=1, st_size=len(ris['text']))
                            self.data[myPath] = ris['text']
                            self.ann_ids[myPath] = ris['ann_id']
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
            for department in self.departments:
                list += [department['name']]
        return list
    
    def rename(self, old, new):
        with requests.Session() as session:
            r = FileManager().update_announcement(url, '9114', session, self.data[old], self.ann_ids[old], new.split('/')[-1], auth)
            if r.status_code == 200:
                self.files[new] = self.files.pop(old)
                self.data[new] = self.data.pop(old)
                self.ann_ids[new] = self.ann_ids.pop(old)

    def truncate(self, path, length, fh=None):
        if length != 0:
            with requests.Session() as session:
                newData = self.data[path][:length]
                if FileManager().update_announcement(url, '9114', session, newData, self.ann_ids[path], path.split('/')[-1], auth).status_code != 200:
                    print('Non ho potuto modificare l\'annuncio!')
                else:
                    self.data[path] = newData
                    self.files[path]['st_size'] = length
     
    def unlink(self, path):
        with requests.Session() as session:
            session.post(url, auth=auth)
            if path.split('/')[-1].split('.')[0] != '':    #permette al vfs di cancellare file temporanei in modo trasparente rispetto al server
                r = FileManager().delete_announcement(url, '9114', session, self.ann_ids[path])
                if r.status_code == 200:
                    self.files.pop(path)
                    self.ann_ids.pop(path)
                    self.data.pop(path)
                    print('\nAnnuncio rimosso')
                else:
                    print('Non ho potuto rimuovere l\'annuncio!')
            else:
                print('\nSto eliminando un file temporaneo')
                self.files.pop(path)
   
    def write(self, path, data, offset, fh):
        with requests.Session() as session:
            newData = self.data[path][:offset] + data
            if len(path.split('/')[-1].split('.')) == 1:
                r = FileManager().update_announcement(url, '9114', session, newData, self.ann_ids[path], path.split('/')[-1], auth)
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
