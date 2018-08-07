import logging
import requests
import time
import platform
import sys
import urllib
from PyQt5 import QtCore, Qt
from distutils.version import LooseVersion
from ui._version import _backup_version

        
class CheckXNASBackupOnline(Qt.QThread):
    finished = QtCore.pyqtSignal(str)
    
    def __init__(self):
        Qt.QThread.__init__(self)
        logging.info('thread_functions.py - CheckXNASBackupOnline - __init__')
    
    def run(self):
        logging.debug('thread_functions.py - CheckXNASBackupOnline - run')
        url = 'https://api.github.com/repos/olivierpascalhenry/XigmaNAS-Conf-Backup/releases/latest'
        try:
            json_object = requests.get(url=url).json()
            format = ''
            if getattr(sys, 'frozen', False) :
                if platform.system() == 'Windows':
                    format = '.msi'
                elif platform.system() == 'Linux':
                    format = '.tar.gz'
            else:
                format = 'sources.zip'
            try:
                if LooseVersion(_backup_version) < LooseVersion(json_object['tag_name']):
                    assets = json_object['assets']
                    download_url = 'no new version'
                    for asset in assets:
                        link = asset['browser_download_url']
                        if format in link:
                            download_url = link  
                    self.finished.emit(download_url)
                else:
                    self.finished.emit('no new version')
            except KeyError:
                self.finished.emit('no new version')
        except Exception:
            logging.exception('thread_functions.py - CheckXNASBackupOnline - run - internet connection error - url ' + url)

    def stop(self):
        logging.debug('thread_functions.py - CheckXNASBackupOnline - stop')
        self.terminate()

        
class DownloadFile(Qt.QThread):
    download_update = QtCore.pyqtSignal(list)
    download_done = QtCore.pyqtSignal()
    download_failed = QtCore.pyqtSignal()
    
    def __init__(self, url_name, update_file=None):
        Qt.QThread.__init__(self)
        logging.info('thread_functions.py - DownloadFile - __init__ - url_name ' + str(url_name)
                      + ' ; update_file ' + str(update_file))
        self.url_name = url_name
        self.update_file = update_file
        self.filename = self.url_name[self.url_name.rfind("/")+1:]
        self.cancel = False
        
    def run(self):
        logging.debug('thread_functions.py - DownloadFile - run - download started')
        if len(self.filename) > 35:
            if platform.system() == 'Windows':
                self.filename = self.filename[:21] + '[...]' + self.filename[-4:]
            elif platform.system() == 'Linux':
                self.filename = self.filename[:21] + '[...]' + self.filename[-7:]
        self.download_update.emit([0, 'Downloading %s...' % self.filename])
        opened_file = open(self.update_file, 'wb')
        try:
            opened_url = urllib.request.urlopen(self.url_name, timeout=10)
            totalFileSize = int(opened_url.info()['Content-Length'])
            bufferSize = 9192
            fileSize = 0
            start = time.time()
            while True:
                if self.cancel:
                    opened_file.close()
                    break
                buffer = opened_url.read(bufferSize)
                if not buffer:
                    break
                fileSize += len(buffer)
                opened_file.write(buffer)
                download_speed = self._set_size(fileSize/(time.time() - start)) + '/s'
                self.download_update.emit([round(fileSize * 100 / totalFileSize), 'Downloading %s at %s' % (self.filename, download_speed)])
            opened_file.close()
            if not self.cancel:
                logging.debug('thread_functions.py - DownloadFile - run - download finished')
                self.download_done.emit()
            else:
                logging.debug('thread_functions.py - DownloadFile - run - download canceled')
        except Exception:
            logging.exception('thread_functions.py - DownloadFile - run - connexion issue ; self.url_name ' + self.url_name)
            opened_file.close()
            self.download_failed.emit()
    
    def _set_size(self, bytes):
        suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        i = 0
        while bytes >= 1024 and i < len(suffixes)-1:
            bytes /= 1024.
            i += 1
        f = ('%.2f' % bytes).rstrip('0').rstrip('.')
        return '%s %s' % (f, suffixes[i])
    
    def cancel_download(self):
        logging.debug('thread_functions.py - DownloadFile - cancel_download')
        self.cancel = True
    
    def stop(self):
        logging.debug('thread_functions.py - DownloadFile - stop')
        self.terminate()
