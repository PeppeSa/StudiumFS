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

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

from src.scraping import FileManager

if not hasattr(__builtins__, 'bytes'):
    bytes = str

auth = {
    'login': raw_input('Nome utente: '),
    'password': getpass('Password: ')
}
url = 'http://studium.unict.it/dokeos/2018/'
switch = {
    2: 'degreeCourse',
    3: 'teaching',
    4: 'file'
}

class Memory(LoggingMixIn, Operations):

    def __init__(self):
        with requests.Session() as session:
            session.post(url, data=auth)
            self.departments = FileManager().get_departments(url, auth, session)
            self.files = {}
            self.data = defaultdict(bytes)
            self.fd = 0
            self.cids = {}
            now = time()
            self.files['/'] = dict(st_mode=(S_IFDIR | 0o755), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=3)
            for department in self.departments:
                self.files['/' + department['name']] = dict(st_mode=(S_IFDIR | 0o755), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=3)
                self.cids['/' + department['name']] = department['cid']

    def getattr(self, path, fh=None):
        if path not in self.files:
            raise FuseOSError(ENOENT)
        return self.files[path]

    def open(self, path, flags):
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
                    session.post(url, data=auth)
                    switchIndex = len(path.split('/'))
                    func_name = switch.get(switchIndex, 'error')
                    result = getattr(FileManager(), 'get_' + func_name + 's')(url, auth, self.cids[path], session)
                    c = 1
                    for ris in result:
                        if func_name is 'file':
                            myPath = path + '/' + ris['title']
                            if myPath in self.files:
                                myPath += '(' + str(c) + ')'
                                c += 1
                            self.files[myPath] = dict(st_mode=(S_IFREG | 0o444), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=1, st_size=len(ris['text']))
                            self.data[myPath] = ris['text']
                        else:
                            myPath = path + '/' + ris['name']
                            if myPath in self.files:
                                myPath += '(' + str(c) + ')'
                                c += 1
                            self.files[myPath] = dict(st_mode=(S_IFDIR | 0o755), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=3)
                            self.cids[myPath] = ris['cid']

            for filePath in self.files:
                if str(path) in str(filePath):
                    print('\nfilePath: ' + filePath)
                    fileName = filePath.split('/')[-1]
                    list += [fileName]
        else:
            for department in self.departments:
                list += [department['name']]
        return list

if __name__ == '__main__':
    if len(argv) != 2:
        print('usage: %s <mountpoint>' % argv[0])
        exit(1)

    logging.basicConfig(level=logging.DEBUG)
    fuse = FUSE(Memory(), argv[1], foreground=True)
