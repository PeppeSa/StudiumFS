from __future__ import print_function, absolute_import, division

import logging
from getpass import getpass

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

url = 'http://studium.unict.it/dokeos/2018/main/'
urlAnnouncements = url + 'announcements/'

class Memory(LoggingMixIn, Operations):

    def __init__(self):     # Crea file e cartelle appena viene montato il VFS
        self.teachings = FileManager().get_teachings()
        self.files = {}
        self.data = defaultdict(bytes)
        self.fd = 0
        now = time()
        self.files['/'] = dict(st_mode=(S_IFDIR | 0o755), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=3)
        for teaching in self.teachings:
            self.files['/' + teaching['name']] = dict(st_mode=(S_IFDIR | 0o755), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=2)
            files_array = FileManager().get_files(urlAnnouncements, auth, teaching['cid'])
            c = 1
            for f in files_array:
                title = f['title']
                if '/' + teaching['name'] + '/' + title in self.files:
                    title += '(' + str(c) + ')'
                    c += 1
                    print('\nHo modificato un nome\n')
                self.files['/' + teaching['name'] + '/' + title] = dict(st_mode=(S_IFREG | 0o444), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=1, st_size=len(f['text']))
                self.data['/' + teaching['name'] + '/' + title] = f['text']
                self.fd += 1

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
        if path != '/':
            for filePath in self.files:
                fileName = filePath.split('/')[-1]
                if str(path) in str(filePath):
                    list += [fileName]
        else:
            for teaching in self.teachings:
                list += [teaching['name']]
        return list

if __name__ == '__main__':
    if len(argv) != 2:
        print('usage: %s <mountpoint>' % argv[0])
        exit(1)

    logging.basicConfig(level=logging.DEBUG)
    fuse = FUSE(Memory(), argv[1], foreground=True)
