import logging
import os
import tempfile
import time
import platform
import shutil
import sys
import paramiko
import datetime
import hashlib
from PyQt5 import QtCore, QtWidgets, QtGui
from ui._version import _backup_version, _eclipse_version, _py_version, _qt_version
from ui.Ui_mainwindow import Ui_MainWindow
from functions.window_functions import MyAbout, MyOptions, MyInfo, MyUpdate, MyWarningUpdate, MyCredentials
from functions.thread_functions import CheckXNASBackupOnline


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, path, config_dict, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.config_dict = config_dict
        self.config_path = path
        logging.info('mainwindow.py - UI initialization ...')
        self.setupUi(self)
        self.backup.clicked.connect(self.backup_configuration_file)
        self.check_downloader_update()
        self.check_file_folder()
        self.populate_folder_target()
        logging.info('mainwindow.py - UI initialized ...')
        logging.info('*****************************************')
    
    @QtCore.pyqtSlot()
    def on_actionExit_triggered(self):
        self.close()
    
    @QtCore.pyqtSlot()
    def on_actionAbout_triggered(self):
        self.open_about()
        
    @QtCore.pyqtSlot()
    def on_actionOptions_triggered(self):
        self.open_options()
    
    @QtCore.pyqtSlot()
    def on_actionUpdate_triggered(self):
        self.download_and_install_update()
    
    def populate_folder_target(self):
        logging.debug('mainwindow.py - populate_folder_target')
        self.label_3.setText(self.config_dict.get('CREDENTIALS', 'folder'))
        self.label_4.setText(self.config_dict.get('CREDENTIALS', 'target'))
    
    def backup_configuration_file(self):
        logging.debug('mainwindow.py - backup_configuration_file')
        target = self.config_dict.get('CREDENTIALS', 'target')
        if target:
            success = False
            failure_reason = ''
            nas_md5 = ''
            password = self.config_dict.get('CREDENTIALS', 'password')
            username = self.config_dict.get('CREDENTIALS', 'username')
            if not password or not username:
                logging.debug('mainwindow.py - backup_configuration_file - username/password missing')
                self.credentialsyWindow = MyCredentials(username, password)
                x1, y1, w1, h1 = self.geometry().getRect()
                _, _, w2, h2 = self.credentialsyWindow.geometry().getRect()
                x2 = x1 + w1/2 - w2/2
                y2 = y1 + h1/2 - h2/2
                self.credentialsyWindow.setGeometry(x2, y2, w2, h2)
                self.credentialsyWindow.exec_()
                if self.credentialsyWindow.username and self.credentialsyWindow.password:
                    username = self.credentialsyWindow.username
                    password = self.credentialsyWindow.password
            if username and password:
                folder = self.config_dict.get('CREDENTIALS', 'folder')
                port = self.config_dict.get('CREDENTIALS', 'target_port')
                y, m, d = str(datetime.datetime.now().year), str(datetime.datetime.now().month), str(datetime.datetime.now().day)
                h, mm, s = str(datetime.datetime.now().hour), str(datetime.datetime.now().minute), str(datetime.datetime.now().second)
                if len(m) == 1:
                    m = '0' + m
                if len(d) == 1:
                    d = '0' + d
                if len(h) == 1:
                    h = '0' + h
                if len(mm) == 1:
                    mm = '0' + mm
                if len(s) == 1:
                    s = '0' + s
                filename = 'configuration_' + target + '_' + y + m + d + 'T' + h + mm + s + '.xml'
                try:
                    try:
                        logging.debug('mainwindow.py - backup_configuration_file - ssh connection...')
                        ssh_client = paramiko.SSHClient()
                        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        ssh_client.connect(hostname=target, username=username, password=password)
                        logging.debug('mainwindow.py - backup_configuration_file - ssh connection established')
                        stdin, stdout, stderr = ssh_client.exec_command('md5 /conf/config.xml')
                        tmp = str(stdout.readlines())
                        if tmp != '[]':
                            index1 = tmp.find('=')
                            nas_md5 = tmp[index1+2:-4]
                            logging.debug('mainwindow.py - backup_configuration_file - MD5 checksum generated')
                        else:
                            failure_reason = str(stderr.readlines())[2:-4]
                            logging.debug('mainwindow.py - backup_configuration_file - MD5 checksum failed')
                        if platform.system() == 'Windows':
                            full_path = folder + '\\' + filename
                            separator = '\\'
                        elif platform.system() == 'Linux':
                            full_path = folder + '/' + filename
                            separator = '/'
                        logging.debug('mainwindow.py - backup_configuration_file - opening sftp')
                        ftp_client=ssh_client.open_sftp()
                        logging.debug('mainwindow.py - backup_configuration_file - sftp opened, requesting file')
                        ftp_client.get('/conf/config.xml', full_path)
                        logging.debug('mainwindow.py - backup_configuration_file - file downloaded')
                        ftp_client.close()
                        ssh_client.close()
                        success = True
                        local_md5 = hashlib.md5(open(full_path,'rb').read()).hexdigest()
                    except paramiko.ssh_exception.AuthenticationException:
                        failure_reason = 'Authentication seems to have failed. Please check the username and/or the password for authentication.'
                        logging.exception('mainwindow.py - backup_configuration_file - AuthenticationException - authentication seems to have failed, check'
                                          + ' username and/or password.')
                    except FileNotFoundError:
                        failure_reason = 'The configuration file has not been found. Please check the path and/or the name of the file.'
                        logging.exception('mainwindow.py - backup_configuration_file - FileNotFoundError - configuration file not found, check the path'
                                            + ' and/or the name of the file.')
                    except PermissionError:
                        failure_reason = 'The account linked to the username and password doesn\'t seem to have sufficient rights to access NAS by SSH.'
                        logging.exception('mainwindow.py - backup_configuration_file - PermissionError - account with insufficient rights.')
                except Exception:
                    failure_reason = 'Download of the configuration file failed for an unknown reason. Please check the log file for details.'
                    logging.exception('mainwindow.py - backup_configuration_file - Exception - an exception has occured.')
                if not success:
                    text = failure_reason
                else:
                    if nas_md5 == local_md5 and nas_md5 != '':
                        text = ('The configuration file has been well backed up in the folder:<br>&nbsp;&nbsp;&nbsp;&nbsp;<b>' + folder + '</b><br>'
                                + 'with the file name:<br>&nbsp;&nbsp;&nbsp;&nbsp;<b>' + filename + '</b>.')
                    else:
                        if nas_md5 == '' and local_md5 == '':
                            text = ('The configuration file has been downloaded in the folder:<br>&nbsp;&nbsp;&nbsp;&nbsp;<b>' + folder + '</b><br>'
                                    + 'with the file name:<br>&nbsp;&nbsp;&nbsp;&nbsp;<b>' + filename + '</b>.<br><br><span style=\" font-weight:600'
                                    + '; color:#c80000;\">The MD5 checksums of the original and downloaded files couldn\'t be checked. Please be car'
                                    + 'efull with this configuration file.</span>')
                        else:
                            if nas_md5 == '':
                                text = ('The configuration file has been downloaded in the folder:<br>&nbsp;&nbsp;&nbsp;&nbsp;<b>' + folder + '</b><br>'
                                        + 'with the file name:<br>&nbsp;&nbsp;&nbsp;&nbsp;<b>' + filename + '</b>.<br><br><span style=\" font-weight:600'
                                        + '; color:#c80000;\">The MD5 checksum of the original file couldn\'t be checked. Please be carefull with this c'
                                        + 'onfiguration file.</span>')
                            elif local_md5 == '':
                                text = ('The configuration file has been downloaded in the folder:<br>&nbsp;&nbsp;&nbsp;&nbsp;<b>' + folder + '</b><br>'
                                        + 'with the file name:<br>&nbsp;&nbsp;&nbsp;&nbsp;<b>' + filename + '</b>.<br><br><span style=\" font-weight:600'
                                        + '; color:#c80000;\">The MD5 checksum of the downloaded file couldn\'t be checked. Please be carefull with this'
                                        + ' configuration file.</span>')
                            else:
                                text = ('The configuration file has been downloaded in the folder:<br>&nbsp;&nbsp;&nbsp;&nbsp;<b>' + folder + '</b><br>'
                                    + 'with the file name:<br>&nbsp;&nbsp;&nbsp;&nbsp;<b>' + filename + '</b>.<br><br><span style=\" font-weight:600; c'
                                    + 'olor:#c80000;\">The MD5 checksums of the original and downloaded files don\'t match. Please be carefull with thi'
                                    + 's configuration file, it can be corrupted.</span>')
                self.infoWindow = MyInfo(text)
                _, _, w, h = QtWidgets.QDesktopWidget().screenGeometry(-1).getRect()
                _, _, w2, h2 = self.infoWindow.geometry().getRect()
                self.infoWindow.setGeometry(w/2 - w2/2, h/2 - h2/2, 600, self.infoWindow.sizeHint().height())
                self.infoWindow.setMinimumSize(QtCore.QSize(600, self.infoWindow.sizeHint().height()))
                self.infoWindow.setMaximumSize(QtCore.QSize(600, self.infoWindow.sizeHint().height()))
                self.infoWindow.exec_()
        
    def open_about(self):
        logging.debug('mainwindow.py - open_about')
        text = ("The following software (v" + _backup_version + ") was developed by Olivier Henry, using Eclipse "
                + _eclipse_version + ", Python " + _py_version + " and PyQt " + _qt_version
                + ". It was designed to make a backup of the configuration file of XigmaNAS"
                + " using Python and scp commands.")
        self.aboutWindow = MyAbout(text)
        x1, y1, w1, h1 = self.geometry().getRect()
        _, _, w2, h2 = self.aboutWindow.geometry().getRect()
        x2 = x1 + w1/2 - w2/2
        y2 = y1 + h1/2 - h2/2
        self.aboutWindow.setGeometry(x2, y2, w2, h2)
        self.aboutWindow.setMinimumSize(QtCore.QSize(850, 450))
        self.aboutWindow.setMaximumSize(QtCore.QSize(850, 450))
        self.aboutWindow.exec_()
        
    def open_options(self):
        logging.debug('mainwindow.py - open_options')
        self.optionWindow = MyOptions(self.config_dict)
        x1, y1, w1, h1 = self.geometry().getRect()
        _, _, w2, h2 = self.optionWindow.geometry().getRect()
        x2 = x1 + w1/2 - w2/2
        y2 = y1 + h1/2 - h2/2
        self.optionWindow.setGeometry(x2, y2, w2, h2)
        self.optionWindow.exec_()
        if not self.optionWindow.cancel:
            self.config_dict = self.optionWindow.config_dict
            with open(os.path.join(self.config_path, 'xigmanas_backup.ini'), 'w') as config_file:
                self.config_dict.write(config_file)
            logging.getLogger().setLevel(self.config_dict.get('LOG', 'level'))
            self.check_downloader_update()
            self.populate_folder_target()
    
    def check_file_folder(self):
        logging.debug('mainwindow.py - check_file_folder')
        if not os.path.isdir(self.config_dict.get('CREDENTIALS', 'folder')) and self.config_dict.get('CREDENTIALS', 'folder'):
            logging.exception('mainwindow.py - check_file_folder - exception occured when the software checked the existence of the backup folder. '
                              + 'Please check that the folder exists. The folder option in the config file is going to be modified to the defa'
                              + 'ult folder.')
            self.config_dict.set('CREDENTIALS', 'folder', '')
            with open(os.path.join(self.config_path, 'xigmanas_backup.ini'), 'w') as config_file:
                        self.config_dict.write(config_file)
            text = ('The software has detected that the folder where XigmaNAS config files are saved doesn\'t exist anymore. It has been reseted in the config file'
                    + ' to the default folder. Please check your options and set a new folder for backup.')
            self.infoWindow = MyInfo(text)
            _, _, w, h = QtWidgets.QDesktopWidget().screenGeometry(-1).getRect()
            _, _, w2, h2 = self.infoWindow.geometry().getRect()
            self.infoWindow.setGeometry(w/2 - w2/2, h/2 - h2/2, 450, self.infoWindow.sizeHint().height())
            self.infoWindow.setMinimumSize(QtCore.QSize(450, self.infoWindow.sizeHint().height()))
            self.infoWindow.setMaximumSize(QtCore.QSize(450, self.infoWindow.sizeHint().height()))
            self.infoWindow.exec_()
    
    def check_downloader_update(self):
        logging.debug('mainwindow.py - check_downloader_update')
        self.actionUpdate.setEnabled(False)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icons/xigmanas_conf_backup_icon.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionUpdate.setIcon(icon)
        self.actionUpdate.setToolTip('')
        if self.config_dict['OPTIONS'].getboolean('check_update'):
            self.check_downloader = CheckXNASBackupOnline()
            self.check_downloader.start()
            self.check_downloader.finished.connect(self.parse_downloader_update)
        else:
            logging.info('mainwindow.py - check_downloader_update - from options, no update check')
                    
    def parse_downloader_update(self, val):
        logging.debug('mainwindow.py - parse_downloader_update - val ' + str(val))
        if val == 'no new version':
            self.actionUpdate.setEnabled(False)
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap("icons/xigmanas_conf_backup_icon.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.actionUpdate.setIcon(icon)
            self.actionUpdate.setToolTip('No update available !')
        elif 'http' in val:
            self.actionUpdate.setEnabled(True)
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap("icons/xigmanas_conf_backup_update_available.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.actionUpdate.setIcon(icon)
            if getattr(sys, 'frozen', False ) :
                self.actionUpdate.setToolTip('A new update is available for XigmaNAS Conf Backup ! Click here to install it automatically.')
            else:
                self.actionUpdate.setToolTip('A new update is available for XigmaNAS Conf Backup ! Click here to download it.')
            self.link_latest_version = val
    
    def download_and_install_update(self):
        logging.debug('mainwindow.py - download_and_install_update - link_latest_version ' + str(self.link_latest_version))
        if self.link_latest_version:
            frozen = False
            height = 250
            if getattr(sys, 'frozen', False) :
                frozen = True
                height = 200
            self.updateWindow = MyWarningUpdate(frozen)
            x1, y1, w1, h1 = self.geometry().getRect()
            _, _, w2, h2 = self.updateWindow.geometry().getRect()
            x2 = x1 + w1/2 - w2/2
            y2 = y1 + h1/2 - h2/2
            self.updateWindow.setGeometry(x2, y2, w2, h2)
            self.updateWindow.setMinimumSize(QtCore.QSize(600, height))
            self.updateWindow.setMaximumSize(QtCore.QSize(600, height))
            self.updateWindow.exec_()
            try:
                if self.updateWindow.buttonName == 'update_button':
                    if getattr(sys, 'frozen', False) :
                        temp_folder = tempfile.gettempdir()
                    else:
                        temp_folder = os.path.expanduser("~")+"/Downloads/"
                    self.downloadWindow = MyUpdate(self.link_latest_version, temp_folder)
                    x1, y1, w1, h1 = self.geometry().getRect()
                    _, _, w2, h2 = self.downloadWindow.geometry().getRect()
                    x2 = x1 + w1/2 - w2/2
                    y2 = y1 + h1/2 - h2/2
                    self.downloadWindow.setGeometry(x2, y2, w2, h2)
                    self.downloadWindow.setMinimumSize(QtCore.QSize(500, self.downloadWindow.sizeHint().height()))
                    self.downloadWindow.setMaximumSize(QtCore.QSize(500, self.downloadWindow.sizeHint().height()))
                    self.downloadWindow.exec_()
                    logging.debug('mainwindow.py - download_and_install_downloader_update - download finished')
                    if not self.downloadWindow.cancel:
                        if getattr(sys, 'frozen', False) :
                            filename = self.link_latest_version[self.link_latest_version.rfind('/')+1:]
                            if platform.system() == 'Windows':
                                os.startfile(temp_folder + '\\' + filename)
                                time.sleep(0.1)
                                self.close()
                            elif platform.system() == 'Linux':
                                shutil.copy('functions/unzip_update.py', temp_folder)
                                install_folder = self.config_path + '/'
                                command = 'python3 ' + temp_folder + '/unzip_update.py ' + temp_folder + '/' + filename + ' ' + install_folder
                                os.system('x-terminal-emulator -e ' + command)
                                time.sleep(0.1)
                                self.close()
                        else:
                            time.sleep(0.1)
                            self.close()
            except AttributeError:
                pass

    def closeEvent(self, event):
        logging.debug('mainwindow.py - closeEvent')
        logging.info('XigmaNAS Conf Backup ' + _backup_version + ' is closing ...')
        self.close()
