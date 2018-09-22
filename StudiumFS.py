from __future__ import print_function, absolute_import, division

import logging

from collections import defaultdict
from errno import ENOENT
from stat import S_IFDIR, S_IFLNK, S_IFREG
from sys import argv, exit
from time import time

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

from src.scraping import FileManager

if not hasattr(__builtins__, 'bytes'):
    bytes = str

auth = {
    'login': raw_input('Nome utente: '),
    'password': raw_input('Password: ')
}
cidReq = '9114'     # Corso di Sistemi Operativi
url = 'http://studium.unict.it/dokeos/2018/main/'
urlAnnouncements = url + 'announcements/'

files_array = FileManager().get_files(urlAnnouncements, auth, cidReq)

class Memory(LoggingMixIn, Operations):

    def __init__(self):     # Crea file e cartelle appena viene montato il VFS
        self.files = {}
        self.data = defaultdict(bytes)
        self.fd = 0
        now = time()
        self.files['/'] = dict(st_mode=(S_IFDIR | 0o755), st_ctime=now,
                               st_mtime=now, st_atime=now, st_nlink=3)
        self.files['/Sistemi Operativi'] = dict(st_mode=(S_IFDIR | 0o755), st_ctime=now,
                               st_mtime=now, st_atime=now, st_nlink=2)
        for f in files_array:
            self.files['/Sistemi Operativi/' + f['title']] = dict(st_mode=(S_IFREG | 0o444), st_ctime=now, st_mtime=now,
                                                            st_atime=now, st_nlink=1, st_size=len(f['text']))
            self.data['/Sistemi Operativi/' + f['title']] = f['text']
            self.fd += 1
        print(self.files)

    def getattr(self, path, fh=None):
        if path not in self.files:
            raise FuseOSError(ENOENT)
        return self.files[path]


    def open(self, path, flags):
        self.fd += 1
        return self.fd

    def read(self, path, size, offset, fh):
        return self.data[path][offset:offset + size]

    def readdir(self, path, fh):    # Codice statico temporaneo, permette di visualizzare i file nella sottocartella 'Sistemi Operativi'
        list = ['.', '..']
        if path != '/':
            for filePath in self.files:
                list += [filePath.split('/')[-1].decode('utf-8')]
        else:
            list += ['Sistemi Operativi']
        return list


if __name__ == '__main__':
    if len(argv) != 2:
        print('usage: %s <mountpoint>' % argv[0])
        exit(1)

    logging.basicConfig(level=logging.DEBUG)
    fuse = FUSE(Memory(), argv[1], foreground=True)
