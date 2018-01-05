#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import os, re, sys, time
from PyQt5.QtCore import *


class TorBootstrap(QThread):
    signal = pyqtSignal(str)
    def __init__(self, main):
        #super(TorBootstrap, self).__init__(main)
        QThread.__init__(self, parent=None)

        #self.signal = SIGNAL("signal")  # Not usable in PyQt5 anymore
        self.previous_status = ''
        self.bootstrap_percent = 0
        #self.is_running = False
        self.control_cookie_path = '/run/tor/control.authcookie'
        self.control_socket_path = '/run/tor/control'
        self.tor_controller = self.connect_to_control_port()

    def connect_to_control_port(self):
        import stem
        import stem.control
        import stem.socket
        from stem.connection import connect

        '''
        In case something wrong happened when trying to start Tor,
        causing /run/tor/control never be generated.
        We set up a time counter and hardcode the wait time limitation as 15s.
        '''
        self.count_time = 0
        while(not os.path.exists(self.control_socket_path) and self.count_time < 15):
            self.previous_status = 'Waiting for /run/tor/control...'
            time.sleep(0.2)
            self.count_time += 0.2

        if os.path.exists(self.control_socket_path):
            self.tor_controller = stem.control.Controller.from_socket_file(self.control_socket_path)
        else:
            print(self.control_socket_path + ' not found!!!')

        if not os.path.exists(self.control_cookie_path):
            # TODO: can we let Tor generate a cookie to fix this situiation?
            print(self.control_cookie_path + ' not found!!!')
        else:
            with open(self.control_cookie_path, "rb") as f:
                cookie = f.read()
            try:
                self.tor_controller.authenticate(cookie)
            except stem.connection.IncorrectCookieSize:
                pass  #if the cookie file's size is wrong
            except stem.connection.UnreadableCookieFile:
                pass  #if # TODO: he cookie file doesn't exist or we're unable to read it
            except stem.connection.CookieAuthRejected:
                pass  #if cookie authentication is attempted but the socket doesn't accept it
            except stem.connection.IncorrectCookieValue:
                pass  #if the cookie file's value is rejected
        return self.tor_controller


    def run(self):
        #self.is_running = True
        while self.bootstrap_percent < 100:
            bootstrap_status = self.tor_controller.get_info("status/bootstrap-phase")
            '''
            bootstrap_status_test = self.tor_controller.get_info("")
            print(bootstrap_status_test)
            '''
            self.bootstrap_percent = int(re.match('.* PROGRESS=([0-9]+).*', bootstrap_status).group(1))
            if bootstrap_status != self.previous_status:
                sys.stdout.write('{0}\n'.format(bootstrap_status))
                sys.stdout.flush()
                self.previous_status = bootstrap_status
                self.signal.emit(bootstrap_status)
            time.sleep(0.2)


def main():
    thread = TorBootstrap()
