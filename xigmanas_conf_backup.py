import logging
import os
import sys
import configparser
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from ui.mainwindow import MainWindow
from ui._version import _backup_version


def launch_data_downloader(path):
    app = QApplication(sys.argv)
    splash_pix = QPixmap('icons/xigmanas_conf_backup_icon.svg')
    splash = QSplashScreen(splash_pix)
    splash.setMask(splash_pix.mask())
    splash.show()
    config_dict = configparser.ConfigParser()
    if not os.path.exists(os.path.join(path, 'xigmanas_backup.ini')):
        config_dict['LOG'] = {'level': 'INFO',
                              'path': ''
                              }
        config_dict['OPTIONS'] = {'language':'english',
                                  'check_update':'False'
                                  }
        config_dict['CREDENTIALS'] = {'password':'',
                                      'username':'',
                                      'folder':'',
                                      'target':'',
                                      'target_port':'22'
                                      }
        with open(os.path.join(path, 'xigmanas_backup.ini'), 'w') as configfile:
            config_dict.write(configfile)
    config_dict.read(os.path.join(path, 'xigmanas_backup.ini'))
    path_exist = True
    if not config_dict.get('LOG', 'path'):
        log_filename = os.path.join(path, 'xigmanas_backup_log.out')
    else:
        path_exist = os.path.isdir(config_dict.get('LOG', 'path'))
        if path_exist:
            log_filename = os.path.join(config_dict.get('LOG', 'path'),'xigmanas_backup_log.out')
        else:
            log_filename = os.path.join(path, 'xigmanas_backup_log.out')
    logging.getLogger('').handlers = []
    logging.basicConfig(filename = log_filename,
                        level = getattr(logging, config_dict.get('LOG', 'level')),
                        filemode = 'w',
                        format = '%(asctime)s : %(levelname)s : %(message)s')
    formatter = logging.Formatter('%(levelname)s : %(message)s')
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    logging.info('*****************************************')
    logging.info('XigmaNAS Conf Backup ' + _backup_version + ' is starting ...')
    logging.info('*****************************************')
    ui = MainWindow(path, config_dict)
    ui.show()
    splash.finish(ui)
    sys.exit(app.exec_())


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception


if __name__ == '__main__':
    path = os.path.abspath(os.path.dirname(__file__))
    launch_data_downloader(path)
    