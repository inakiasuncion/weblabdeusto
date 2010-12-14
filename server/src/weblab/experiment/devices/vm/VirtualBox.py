#!/usr/bin/python
# -*- coding: utf-8 -*-
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
# Author: Luis Rodriguez <luis.rodriguez@opendeusto.es>
#         Pablo Orduña <pablo@ordunya.com>
# 

import subprocess

from VirtualMachineManager import VirtualMachineManager
from voodoo.override import Override

DEBUG = True

VBOXMANAGE_COMMAND_NAME  = 'vboxmanage_command'
VBOXMANAGE_COMMAND_DEFAULT_VALUE = 'VBoxManage' # Could be something like r'c:\Program Files\VirtualBox\VBoxManage' or similar

VBOX_VM_NAME = 'vbox_vm_name'
VBOX_VM_DEFAULT_VALUE = 'weblab'
VBOX_VM_BASE_SNAPSHOT = 'Snapshot 1'



# Note: These functions make use of the VBoxManage utility, which comes with VirtualBox
# It should hence be accessible. Under windows, it will often have to be added to the PATH
# environment variable.

class VirtualBox(VirtualMachineManager):
    
    def __init__(self, cfg_manager):
        VirtualMachineManager.__init__(self, cfg_manager)

        self.vboxmanage       = cfg_manager.get_value(VBOXMANAGE_COMMAND_NAME, VBOXMANAGE_COMMAND_DEFAULT_VALUE)
        self.vm_name          = cfg_manager.get_value(VBOX_VM_NAME, VBOX_VM_DEFAULT_VALUE)
        self.vm_base_snapshot = cfg_manager.get_value(VBOX_VM_BASE_SNAPSHOT, VBOX_VM_BASE_SNAPSHOT)

    @Override(VirtualMachineManager)
    def launch_vm(self):
        """
        Launches the VirtualMachine. Does not wait until the virtual OS is ready. It is hence
        possible, and likely, for this function to return a relatively long time before
        the Virtual Machine is truly ready for usage.
        """
        process = subprocess.Popen([self.vboxmanage,'startvm',self.vm_name])
        process.wait()
    
    @Override(VirtualMachineManager)
    def kill_vm(self):
        process = subprocess.Popen([self.vboxmanage,'controlvm',self.vm_name,'poweroff'])
        process.wait()
            
    @Override(VirtualMachineManager)
    def is_alive_vm(self):
        process = subprocess.Popen([self.vboxmanage,'-q','list','runningvms'], stdout=subprocess.PIPE)
        process.wait()
        lines = process.stdout.readlines()
        if DEBUG: print "running: " + str(lines)
        running = [ line.split('"')[1] for line in lines ]
        return self.vm_name in running

    @Override(VirtualMachineManager)
    def prepare_vm(self):
        if DEBUG:
            print "RESTORING ", self.vm_base_snapshot, " FOR ", self.vm_name
        process = subprocess.Popen([self.vboxmanage, 'snapshot', self.vm_name, "restore", self.vm_base_snapshot])
        process.wait()
    
