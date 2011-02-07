#!/usr/bin/env python
#-*-*- encoding: utf-8 -*-*-
#
# Copyright (C) 2005-2009 University of Deusto
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# This software consists of contributions made by many individuals, 
# listed below:
#
# Author: Pablo Orduña <pablo@ordunya.com>
#

import threading
import time
import weakref
import voodoo.LogLevel as LogLevel
import voodoo.log as log
from voodoo.ResourceManager import is_testing

from weblab.user_processing.coordinator.ResourcesChecker import ResourcesChecker

def sleep(t): # For testing purposes
    time.sleep(t)

class ResourcesCheckerThread(threading.Thread):
    Checker = ResourcesChecker

    def __init__(self):
        threading.Thread.__init__(self)
        self.frequency   = None # Seconds
        self.coordinator = None
        self.stopping    = False

    def run(self):
        while not self.stopping:
            try:
                sleep(1)
                if self.frequency is None:
                    continue
                # Here self.frequency is configured, so wait the rest of the required time
                if self.frequency > 1:
                    sleep(self.frequency - 1)

                if self.stopping:
                    break
                
                if self.coordinator is None:
                    continue

                coordinator = self.coordinator()
                if coordinator is None:
                    continue # coordinator not configured yet
                checker = self.Checker(coordinator)
                checker.check()
            except Exception, e:
                log.log(ResourcesCheckerThread, LogLevel.Critical,
                    "Exception checking resources: %s" % e )
                log.log_exc(ResourcesCheckerThread, LogLevel.Error)

checker_thread = None

def reset():
    global checker_thread
    checker_thread = ResourcesCheckerThread()
    checker_thread.setDaemon(True)
    checker_thread.start()

def clean():
    global checker_thread
    if checker_thread is not None:
        checker_thread.stopping = True
    checker_thread = None

if not is_testing():
    reset()

def set_coordinator(coordinator, new_frequency):
    if checker_thread is not None:
        checker_thread.frequency   = new_frequency
        checker_thread.coordinator = weakref.ref(coordinator)
