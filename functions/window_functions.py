import logging
import os
import time
import platform
from ui.Ui_infowindow import Ui_infoWindow
from ui.Ui_aboutlogwindow import Ui_aboutlogWindow
from ui.Ui_optionwindow import Ui_optionWindow
from ui.Ui_updatewindow import Ui_updateWindow
#from ui.Ui_downloadwindow import Ui_downloadWindow
from ui.Ui_storewindow import Ui_storeWindow
#from ui.Ui_successwindow import Ui_successWindow
from ui.Ui_credentialswindow import Ui_credentialsWindow
from PyQt5 import QtWidgets, QtCore, QtGui
from functions.thread_functions import DownloadFile


class MyInfo(QtWidgets.QDialog, Ui_infoWindow):
    def __init__(self, infoText):
        logging.info('window_functions.py - MyInfo - __init__')
        QtWidgets.QWidget.__init__(self)
        self.setupUi(self)
        self.iw_label_1.setText(infoText)
        self.iw_okButton.clicked.connect(self.closeWindow)
        
    def closeWindow(self):
        logging.info('window_functions.py - MyInfo - closeWindow')
        self.close()

        
class MyAbout(QtWidgets.QDialog, Ui_aboutlogWindow):
    def __init__(self, text):
        logging.info('window_functions.py - MyAbout - __init__')
        QtWidgets.QWidget.__init__(self)
        self.setupUi(self)
        self.label_1.setText(text)
        self.browser.setPlainText(open("documentation/changelog.txt").read())
        self.button.clicked.connect(self.closeWindow)

    def closeWindow(self):
        logging.debug('window_functions.py - MyAbout - closeWindow')
        self.close()





class MyOptions(QtWidgets.QDialog, Ui_optionWindow):
    def __init__(self, config_dict, info_text):
        logging.info('window_functions.py - MyOptions - __init__')
        QtWidgets.QWidget.__init__(self)
        self.setupUi(self)
        self.config_dict = config_dict
        self.info_text = info_text
        itemDelegate = QtWidgets.QStyledItemDelegate()
        self.ow_comboBox_1.setItemDelegate(itemDelegate)
        self.ok_button.clicked.connect(self.save_and_close)
        self.cancel_button.clicked.connect(self.close_window)
        self.open_button_1.clicked.connect(self.get_directory)
        self.open_button_2.clicked.connect(self.get_directory)
        all_info_boxes = self.findChildren(QtWidgets.QToolButton)
        for widget in all_info_boxes:
            if 'info_button' in widget.objectName():
                widget.clicked.connect(lambda: self.info_button())
        self.cancel = True
        self.read_config_dict()
        self.setTabOrder(self.line_1,self.line_2)
        self.setTabOrder(self.line_2,self.line_4)
        self.setTabOrder(self.line_4,self.line_5)
        self.setTabOrder(self.line_5,self.line_6)
        self.setTabOrder(self.line_6,self.line_7)
        self.line_1.setFocus()
    
    def read_config_dict(self):
        logging.debug('window_functions.py - MyOptions - read_config_dict')
        log_level = self.config_dict.get('LOG', 'level')
        log_path = self.config_dict.get('LOG', 'path')
        check_update = self.config_dict['OPTIONS'].getboolean('check_update')
        password = self.config_dict.get('CREDENTIALS', 'password')
        username = self.config_dict.get('CREDENTIALS', 'username')
        folder = self.config_dict.get('CREDENTIALS', 'folder')
        target = self.config_dict.get('CREDENTIALS', 'target')
        port = self.config_dict.get('CREDENTIALS', 'target_port')
        self.ow_comboBox_1.setCurrentIndex(self.ow_comboBox_1.findText(log_level))
        self.line_1.setText(log_path)
        self.line_2.setText(username)
        self.line_4.setText(password)
        self.line_5.setText(target)
        self.line_6.setText(port)
        self.line_7.setText(folder)
        self.checkbox.setChecked(check_update)
    
    def get_directory(self):
        logging.debug('window_functions.py - MyOptions - get_directory')
        file_dialog = QtWidgets.QFileDialog()
        out_dir = file_dialog.getExistingDirectory(self, "Select Directory")
        if self.sender().objectName() == 'open_button_1':
            self.line_1.setText(str(out_dir.replace('/','\\')))
        elif self.sender().objectName() == 'open_button_2':
            self.line_7.setText(str(out_dir.replace('/','\\')))
    
    def save_and_close(self):
        logging.debug('window_functions.py - MyOptions - save_and_close')
        self.cancel = False
        self.config_dict.set('LOG', 'level', str(self.ow_comboBox_1.currentText()))
        self.config_dict.set('LOG', 'path', str(self.line_1.text()))
        self.config_dict.set('OPTIONS', 'check_update', str(self.checkbox.isChecked()))
        self.config_dict.set('CREDENTIALS', 'password', str(self.line_4.text()))
        self.config_dict.set('CREDENTIALS', 'username', str(self.line_2.text()))
        self.config_dict.set('CREDENTIALS', 'target', str(self.line_5.text()))
        self.config_dict.set('CREDENTIALS', 'target_port', str(self.line_6.text()))
        self.config_dict.set('CREDENTIALS', 'folder', str(self.line_7.text()))
        self.close_window()
    
    def info_button(self):
        logging.debug('window_functions.py - MyOptions - info_button - self.sender().objectName() ' + self.sender().objectName())
        if 'infoButton' in self.sender().objectName():
            x = QtGui.QCursor.pos().x()
            y = QtGui.QCursor.pos().y()
            x = x - 175
            y = y + 50
            self.infoWindow = MyInfo(self.info_text[self.sender().objectName()])
            self.infoWindow.setMinimumSize(QtCore.QSize(450, self.infoWindow.sizeHint().height()))
            self.infoWindow.setMaximumSize(QtCore.QSize(450, self.infoWindow.sizeHint().height()))
            self.infoWindow.setGeometry(x, y, 450, self.infoWindow.sizeHint().height())
            self.infoWindow.exec_()
    
    def close_window(self):
        logging.info('window_functions.py - MyOptions - close_window')
        self.close()


class MyUpdate(QtWidgets.QDialog, Ui_storeWindow):
    def __init__(self, url, folder):
        logging.info('window_functions.py - MyUpdate - __init__')
        QtWidgets.QWidget.__init__(self)
        self.setupUi(self)
        self.temp_folder = folder
        self.url = url
        if platform.system() == 'Windows':
            self.update_file = self.temp_folder + '\\' + self.url[self.url.rfind('/')+1:]
        elif platform.system() == 'Linux':
            self.update_file = self.temp_folder + '/' + self.url[self.url.rfind('/')+1:]
        self.sw_button.clicked.connect(self.cancel_download)
        self.cancel = False
        self.download_update()
    
    def update_progress_bar(self, val):
        if isinstance(val, list):
            self.progressBar.setValue(val[0])
            self.sw_label.setText(val[1])
        else:
            self.progressBar.setValue(val)
    
    def download_update(self):
        logging.debug('window_functions.py - MyUpdate - download_update')
        self.thread = DownloadFile(self.url, self.update_file)
        self.thread.download_update.connect(self.update_progress_bar)
        self.thread.download_done.connect(self.close)
        self.thread.download_failed.connect(self.download_failed)
        self.thread.start()
    
    def cancel_download(self):
        logging.debug('window_functions.py - MyUpdate - cancel_download')
        self.thread.cancel_download()
        self.cancel = True
        time.sleep(0.25)
        self.close()
        
    def download_failed(self):
        logging.debug('window_functions.py - MyUpdate - download_failed')
        self.update_progress_bar(0)
        self.sw_label.setText('Download failed')
        self.cancel_download()
        
    def closeEvent(self, event):
        logging.info('window_functions.py - MyUpdate - closeEvent')
        self.thread.download_update.disconnect(self.update_progress_bar)
        if self.cancel:
            os.remove(self.update_file)





class MyWarningUpdate(QtWidgets.QDialog, Ui_updateWindow):
    def __init__(self, frozen):
        logging.info('window_functions.py - MyWarningUpdate - __init__')
        QtWidgets.QWidget.__init__(self)
        self.setupUi(self)
        if not frozen:
            self.label_1.setText('<p>Click on <b>Download</b> to download the latest update from GitHub repository.</p>'
                                 + '<p>Once the download is over, the software will close automatically. The package is'
                                 + ' downloaded in the <b>Download</b> folder of your operating system. You will have t'
                                 + 'o uncompress it and move all files in the directory of <b>XigmaNAS Conf Backup</b>'
                                 + '. Do not delete <i>xigmanas_backup.ini</i> if you want to keep all your options.</p>')
            self.update_button.setText('Download')
        self.update_button.clicked.connect(self.closeWindow)
        self.cancel_button.clicked.connect(self.closeWindow)
        
    def closeWindow(self):
        logging.info('window_functions.py - MyWarningUpdate - closeWindow')
        self.buttonName = self.sender().objectName()
        self.close()



        
        
class MyCredentials(QtWidgets.QDialog, Ui_credentialsWindow):
    def __init__(self, user, password):
        QtWidgets.QWidget.__init__(self)
        logging.info('mainwindow.py - MyCredentials - __init__')
        self.setupUi(self)
        if user:
            self.edit_1.setText(user)
        if password:
            self.edit_2.setText(password)
        self.username = ''
        self.password = ''
        self.submit.clicked.connect(self.set_username_password)
        self.cancel.clicked.connect(self.closeWindow)

    def set_username_password(self):
        logging.debug('window_functions.py - MyCredentials - set_username_password')
        self.username = str(self.edit_1.text())
        self.password = str(self.edit_2.text())
        self.closeWindow()

    def closeWindow(self):
        logging.info('window_functions.py - MyCredentials - closeWindow')
        self.close()
