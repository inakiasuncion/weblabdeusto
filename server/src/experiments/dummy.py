#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005 onwards University of Deusto
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

import weblab.configuration_doc as configuration_doc
import weblab.experiment.experiment as Experiment

from voodoo.override import Override

class DummyExperiment(Experiment.Experiment):
    def __init__(self, coord_address, locator, cfg_manager, *args, **kwargs):
        super(DummyExperiment, self).__init__(*args, **kwargs)
        self.cfg_manager = cfg_manager
        self.verbose           = cfg_manager.get_value('dummy_verbose', True)
        self.server_identifier = cfg_manager.get_doc_value(configuration_doc.CORE_UNIVERSAL_IDENTIFIER_HUMAN)

    @Override(Experiment.Experiment)
    def do_get_api(self):
        return "1"

    @Override(Experiment.Experiment)
    def do_start_experiment(self, *args, **kwargs):
        if self.verbose:
            print "Experiment started"

    @Override(Experiment.Experiment)
    def do_send_command_to_device(self, command):
        if self.verbose:

            print "Received command: %s" % command

        if command == 'server_info':
            return self.server_identifier

        return "Received command: %s" % command

    @Override(Experiment.Experiment)
    def do_send_file_to_device(self, content, file_info):
        if self.verbose:
            print "Received file with len: %s and file_info: %s" % (len(content), file_info)
        return "Received file with len: %s and file_info: %s" % (len(content), file_info)

    @Override(Experiment.Experiment)
    def do_dispose(self):
        if self.verbose:
            print "dispose"


