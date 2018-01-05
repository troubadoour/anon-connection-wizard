#!/usr/bin/python3 -u

import sys, fileinput
import os, time
from subprocess import call
from anonconnectionwizard import repair_torrc

def tor_status():
    if not os.path.exists('/etc/tor/torrc'):
        return 'no_torrc'

    fh = open('/etc/tor/torrc','r')
    lines = fh.readlines()
    fh.close()

    line_exists = False
    for line in lines:
        if line.strip() == '#DisableNetwork 0':
            line_exists = True
            return 'tor_disabled'
        elif line.strip() == 'DisableNetwork 0':
            line_exists = True
            return 'tor_enabled'

    if not line_exists:
        return 'bad_torrc'

'''Unlike tor_status() function which only shows the current state of the /etc/tor/torrc,
set_enabled() and set_disabled() function will try to repair the missing torrc or
DisableNetwork line by calling repair_torrc module.
This makes sense because when we call set_enabled() or set_disabled() we really want Tor to work,
rather than receive a 'no_torrc' or 'bad_torrc' complain, which is not helpful for users.
'''
def set_enabled():
    repair_torrc.repair_torrc()  # This gurantees a good torrc

    fh = open('/etc/tor/torrc','r')
    lines = fh.readlines()
    fh.close()

    for line in lines:
        if line.strip() == 'DisableNetwork 0':

            command = 'systemctl --no-pager restart tor@default'
            tor_status = call(command, shell=True)

            if tor_status != 0:
                return 'cannot_connect'

            command = 'systemctl --no-pager status tor@default'
            tor_status = call(command, shell=True)

            if tor_status != 0:
                return 'cannot_connect'

            return 'tor_already_enabled'

        elif line.strip() == '#DisableNetwork 0':

            for i, line in enumerate(fileinput.input('/etc/tor/torrc', inplace=1)):
                sys.stdout.write(line.replace('#DisableNetwork 0', 'DisableNetwork 0'))

            command = 'systemctl --no-pager restart tor@default'
            tor_status = call(command, shell=True)

            if tor_status != 0:
                return 'cannot_connect'

            command = 'systemctl --no-pager status tor@default'
            tor_status = call(command, shell=True)

            if tor_status != 0:
                return 'cannot_connect'

            return 'tor_enabled'

    return 'missing_disablenetwork_line'

def set_disabled():
    repair_torrc.repair_torrc()  # This gurantees a good torrc

    fh = open('/etc/tor/torrc','r')
    lines = fh.readlines()
    fh.close()

    for line in lines:
        if line.strip() == '#DisableNetwork 0':
            return 'tor_already_disabled'

        elif line.strip() == 'DisableNetwork 0':
            for i, line in enumerate(fileinput.input('/etc/tor/torrc', inplace=1)):
                sys.stdout.write(line.replace('DisableNetwork 0', '#DisableNetwork 0'))

            command = 'systemctl --no-pager stop tor@default'
            call(command, shell=True)

            return 'tor_disabled'
