#!/usr/bin/python3 -u

'''
This product is produced independently from the Tor® anonymity software and carries no guarantee from The Tor Project about quality, suitability or anything else.

You can verify the original source of Tor for yourselves by visiting the official Tor website: https://www.torproject.org/
'''

from PyQt5 import QtCore
from PyQt5.QtWidgets import *

import sys, os
import re
from subprocess import Popen, PIPE
import time

from anonconnectionwizard import tor_bootstrap


class RestartTor(QWidget):
    def __init__(self):
        super().__init__()

        self.text = QLabel(self)
        self.bootstrap_progress = QProgressBar(self)
        self.layout = QGridLayout()

        self.setupUI()

    def setupUI(self):
        self.setGeometry(300, 150, 450, 150)
        self.setWindowTitle('Restart tor')

        self.text.setWordWrap(True)
        self.text.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.text.setMinimumSize(0, 120)

        self.bootstrap_progress.setMinimumSize(400, 0)
        self.bootstrap_progress.setMinimum(0)
        self.bootstrap_progress.setMaximum(100)

        self.layout.addWidget(self.text, 0, 1, 1, 2)
        self.layout.addWidget(self.bootstrap_progress, 1, 1, 1, 1)
        self.setLayout(self.layout)

        self.restart_tor()

    def center(self):
        rectangle = self.frameGeometry()
        center_point = QDesktopWidget().availableGeometry().center()
        rectangle.moveCenter(center_point)
        self.move(rectangle.topLeft())

    def update_bootstrap(self, status):
        if status != 'timeout':
            bootstrap_phase = re.search(r'SUMMARY=(.*)', status).group(1)
            bootstrap_percent = int(re.match('.* PROGRESS=([0-9]+).*', status).group(1))
            if bootstrap_percent == 100:
                self.text.setText('<p><b>Tor bootstrapping done</b></p>Bootstrap phase: {0}'.format(bootstrap_phase))
                self.bootstrap_done = True
            else:
                self.text.setText('<p><b>Bootstrapping Tor...</b></p>Bootstrap phase: {0}'.format(bootstrap_phase))
            self.bootstrap_progress.setValue(bootstrap_percent)
        else:
            self.bootstrap_timeout = True

    def close(self):
        time.sleep(2)
        sys.exit()

    def restart_tor(self):
        '''
        Restart tor.
        Use subprocess.Popen instead of subprocess.call in order to catch
        possible errors from "restart tor" command.
        '''
        command = Popen(['sudo', 'systemctl', 'restart', 'tor@default'], stdout=PIPE, stderr=PIPE)
        stdout, stderr = command.communicate()

        std_err = "b''"
        stderr = str(stderr)
        command_success = stderr == std_err

        if not command_success:
            # Format stderr for readability in message box.
            stderr = re.sub(r'\n', stderr, ' \n')[3:][:-1]
            error = QMessageBox(QMessageBox.Critical, 'Restart tor', stderr, QMessageBox.Ok)
            error.exec_()
            self.close()

        self.bootstrap_thread = tor_bootstrap.TorBootstrap(self)
        self.bootstrap_thread.signal.connect(self.update_bootstrap)
        self.bootstrap_thread.finished.connect(self.close)
        self.bootstrap_thread.start()

        self.show()
        self.center()


def main():
    app = QApplication(sys.argv)
    restart_tor = RestartTor()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
