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
#         Jaime Irurzun <jaime.irurzun@gmail.com>
#         Luis Rodriguez <luis.rodriguez@opendeusto.es>
#

from voodoo.gen.caller_checker import caller_check
from voodoo.log import logged
from voodoo.override import Override
import experiments.ud_xilinx.exc as UdXilinxExperimentErrors
from experiments.ud_xilinx.command_senders import UdXilinxCommandSender
from experiments.ud_xilinx.programmers import UdXilinxProgrammer
import os
import tempfile
import voodoo.log as log
import weblab.data.server_type as ServerType
import weblab.experiment.exc as ExperimentErrors
import weblab.experiment.experiment as Experiment
import weblab.experiment.util as ExperimentUtil
import weblab.experiment.devices.xilinx_impact.devices as XilinxDevices
import weblab.experiment.devices.xilinx_impact.impact as XilinxImpact
from experiments.xilinxc.compiler import Compiler

import json
import base64
import time

import sys
import traceback

import watertank_simulation

from voodoo.threaded import threaded


# Though it would be slightly more efficient to use single characters, it's a text protocol
# after all, so we will use words for readability.
STATE_NOT_READY = "not_ready"
STATE_AWAITING_CODE = "awaiting_code"
STATE_SYNTHESIZING = "synthesizing"
STATE_SYNTHESIZING_ERROR = "synthesizing_error"
STATE_PROGRAMMING = "programming"
STATE_READY = "ready"
STATE_FAILED = "failed"

# Names for the configuration variables.
CFG_XILINX_COMPILING_FILES_PATH = "xilinx_compiling_files_path"
CFG_XILINX_COMPILING_TOOLS_PATH = "xilinx_compiling_tools_path"

DEBUG = False


#TODO: which exceptions should the user see and which ones should not?
class UdXilinxExperiment(Experiment.Experiment):


    @Override(Experiment.Experiment)
    @caller_check(ServerType.Laboratory)
    @logged("info")
    def do_get_api(self):
        return "2"

    def __init__(self, coord_address, locator, cfg_manager, *args, **kwargs):
        super(UdXilinxExperiment,self).__init__(*args, **kwargs)
        self._coord_address = coord_address
        self._locator = locator
        self._cfg_manager = cfg_manager

        self._device_name, self._xilinx_device, self._xilinx_impact = self._load_xilinx_device()
        self._programmer = self._load_programmer()
        self._command_sender = self._load_command_sender()
        self.webcam_url = self._load_webcam_url()

        self._programming_thread = None
        self._current_state = STATE_NOT_READY
        self._programmer_time = self._cfg_manager.get_value('xilinx_programmer_time', "25") # Seconds
        self._synthesizer_time = self._cfg_manager.get_value('xilinx_synthesizer_time', "90") # Seconds
        self._adaptive_time = self._cfg_manager.get_value('xilinx_adaptive_time', True)
        self._switches_reversed = self._cfg_manager.get_value('switches_reversed', False) # Seconds
        
        self._compiling_files_path = self._cfg_manager.get_value(CFG_XILINX_COMPILING_FILES_PATH, "")
        self._compiling_tools_path = self._cfg_manager.get_value(CFG_XILINX_COMPILING_TOOLS_PATH, "")
        self._synthesizing_result = ""
        
        self._ucf_file = None
        
        self._switches_state = "0000000000"
        
        # These are only for led-state reading. This is an experimental
        # feature.
        self._led_reader = None
        self._led_state = None
        
        # These are for virtual-worlds
        self._virtual_world = ""
        self._virtual_world_state = "";
        self._watertank = None
        

    def _load_xilinx_device(self):
        device_name = self._cfg_manager.get_value('weblab_xilinx_experiment_xilinx_device')
        devices = [ i for i in XilinxDevices.getXilinxDeviceValues() if i == device_name ]
        if len(devices) == 1:
            return device_name, devices[0], XilinxImpact.create(devices[0], self._cfg_manager)
        else:
            raise UdXilinxExperimentErrors.InvalidXilinxDeviceError(device_name)

    def _load_programmer(self):
        device_name = self._cfg_manager.get_value('xilinx_device_to_program')
        return UdXilinxProgrammer.create(device_name, self._cfg_manager, self._xilinx_impact)

    def _load_command_sender(self):
        device_name = self._cfg_manager.get_value('xilinx_device_to_send_commands')
        return UdXilinxCommandSender.create(device_name, self._cfg_manager)

    def _load_webcam_url(self):
        cfg_webcam_url = "%s_webcam_url" % self._xilinx_device.lower()
        return self._cfg_manager.get_value(cfg_webcam_url, "http://localhost")

    def get_state(self):
        return self._current_state

    @Override(Experiment.Experiment)
    @caller_check(ServerType.Laboratory)
    @logged("info",except_for='file_content')
    def do_send_file_to_device(self, file_content, file_info):
        """
        Will spawn a new thread which will program the xilinx board with the
        provided file.
        """
        
        # TODO:
        # We will distinguish the file type according to its size.
        # This is an extremely bad method, which should be changed in the
        # future. Currently we assume that if the file length is small,
        # then it's a VHDL file rather than a BITSTREAM. Explicit UCF
        # is not yet supported.
        extension = file_info
        if extension == "vhd":
            try:
                if DEBUG: print "[DBG]: File received: Info: " + file_info
                self._handle_vhd_file(file_content, file_info)
                return "STATE=" + STATE_SYNTHESIZING
            except Exception as ex:
                if DEBUG: print "EXCEPTION: " + ex
                raise ex
        else:
            self._programming_thread = self._program_file_t(file_content)
            return "STATE=" + STATE_PROGRAMMING
        
    def _handle_ucf_file(self, file_content, file_info):
        print os.getcwd()
        c = Compiler(self._compiling_files_path)
        content = base64.b64decode(file_content)
        c.feed_ucf(content)
        
    def _handle_vhd_file(self, file_content, file_info):
        if DEBUG: print "[DBG] In _handle_vhd_file. Info is " + file_info
        self._compile_program_file_t(file_content)
        
    @threaded()
    @logged("info",except_for='file_content')
    def _compile_program_file_t(self, file_content):
        """
        Running in its own thread, this method will compile the provided
        VHDL code and then program the board if the result is successful.
        """
        self._current_state = STATE_SYNTHESIZING
        c = Compiler(self._compiling_files_path, self._compiling_tools_path)
        #c.DEBUG = True
        content = base64.b64decode(file_content)
        c.feed_vhdl(content)
        if DEBUG: print "[DBG]: VHDL fed. Now compiling."
        success = c.compileit()
        if(not success):
            self._current_state = STATE_SYNTHESIZING_ERROR
            self._compiling_result = c.errors()
        else:
            # If we are using adaptive timing, modify it according to this last input.
            # TODO: Consider limiting the allowed range of variation, in order to dampen potential anomalies.
            elapsed = c.get_time_elapsed()
            if(self._adaptive_time):
                self._programmer_time = elapsed
            
            bitfile = c.retrieve_bitfile()
            if DEBUG: print "[DBG]: .BIT retrieved after successful compile. Now programming."
            c._compiling_result = "Synthesizing done."
            self._program_file_t(bitfile)
        

    @threaded()
    @logged("info",except_for='file_content')
    def _program_file_t(self, file_content):
        """
        Running in its own thread, this method will program the board
        while updating the state of the experiment appropriately.
        """
        try:
            start_time = time.time() # To track the time it takes
            self._current_state = STATE_PROGRAMMING
            self._program_file(file_content)
            self._current_state = STATE_READY
            elapsed = time.time() - start_time # Calculate the time the programming process took
            
            # If we are in adaptive mode, change the programming time appropriately.
            # TODO: Consider limiting the variation range to dampen anomalies.
            if(self._adaptive_time):
                self._programmer_time = elapsed
        except Exception as e:
            # Note: Currently, running the fake xilinx will raise this exception when
            # trying to do a CleanInputs, for which apparently serial is needed.
            self._current_state = STATE_FAILED
            log.log(UdXilinxExperiment, log.level.Warning, "Error programming file: " + str(e) )
            log.log_exc(UdXilinxExperiment, log.level.Warning )

    # This is used in the demo experiment
    def _program_file(self, file_content):
        try:
            fd, file_name = tempfile.mkstemp(prefix='ud_xilinx_experiment_program', suffix='.' + self._xilinx_impact.get_suffix())
            try:
                try:
                    #TODO: encode? utf8?
                    if isinstance(file_content, unicode):
                        file_content_encoded = file_content.encode('utf8')
                    else:
                        file_content_encoded = file_content
                    file_content_recovered = ExperimentUtil.deserialize(file_content_encoded)
                    os.write(fd, file_content_recovered)
                finally:
                    os.close(fd)
                self._programmer.program(file_name)
            finally:
                os.remove(file_name)
                # print file_name
                # import sys
                # sys.stdout.flush()
        except Exception as e:

            #TODO: test me
            log.log( UdXilinxExperiment, log.level.Info,
                "Exception joining sending program to device: %s" % e.args[0])
            log.log_exc( UdXilinxExperiment, log.level.Debug)
            raise ExperimentErrors.SendingFileFailureError( "Error sending file to device: %s" % e)
        self._clear()

    def _clear(self):
        try:
            self._command_sender.send_command("CleanInputs")
        except Exception as e:
            raise ExperimentErrors.SendingCommandFailureError(
                "Error sending command to device: %s" % e
            )


    @Override(Experiment.Experiment)
    @logged("info")
    def do_dispose(self):
        """
        We make sure that the board programming thread has finished, just
        in case the experiment finished early and its still on it.
        """
        if self._programming_thread is not None:
            self._programming_thread.join()
            # Cleaning references
            self._programming_thread = None
            
        if self._watertank is not None:
            # In case it is running.
            self._watertank.autoupdater_stop()
            
        return "ok"


    @Override(Experiment.Experiment)
    @logged("info")
    def do_start_experiment(self, *args, **kwargs):
        self._current_state = STATE_NOT_READY
        return json.dumps({ "initial_configuration" : """{ "webcam" : "%s", "expected_programming_time" : %s, "expected_synthesizing_time" : %s }""" % (self.webcam_url, self._programmer_time, self._synthesizer_time), "batch" : False })


    def _load_led_reading_support(self):
        """
        Will load the modules required to do image processing for reading the led state.
        For this, PIL is needed as a dependency. 
        Also, it is currently in a very experimental state, and cannot 
        really be configured for different boards.
        """
        if self._led_reader != None:
            return
        
        from ledreader import LedReader
        pld_leds = [ (111, 140), (139, 140), (167, 140), (194, 140), (223, 140), (247, 139) ]
        fpga_leds = [ (84, 171), (93, 171), (97, 171), (110, 171), (120, 171), (129, 171), (138, 171), (147, 171) ]
        fpga = "https://www.weblab.deusto.es/webcam/proxied.py/fpga1?-665135651"
        pld = "https://www.weblab.deusto.es/webcam/proxied/pld1?1696782330"
        if self._device_name == "FPGA":
            self._led_reader = LedReader(fpga, fpga_leds, 5, 7)
        elif self._device_name == "PLD":
            self._led_reader = LedReader(pld, pld_leds, 10, 30)
        

    @logged("info")
    @Override(Experiment.Experiment)
    @caller_check(ServerType.Laboratory)
    def do_send_command_to_device(self, command):
        try:
            # Reply with the current state of the experiment. Particularly, the clients
            # will need to know whether the programming has been done and whether we are
            # hence ready to start receiving real commands.
            if command == 'STATE':
                if(DEBUG):
                    print "[DBG]: STATE CHECK: " + self._current_state
                reply = "STATE="+ self._current_state
                return reply
            
            elif command.startswith('ChangeSwitch'):
                # Intercept the ChangeSwitch command to track the state of the Switches.
                # This command will in fact be later relied to the Device.
                cs = command.split(" ");
                switch_number = cs[2]
                if(cs[1] == "on"):
                    self._switches_state[switch_number] = 1
                else:
                    self._switches_state[switch_number] = 0
                    
            elif command == 'REPORT_SWITCHES':
                return self._switches_state
            
            elif command.startswith('VIRTUALWORLD_MODE'):
                vw = command.split(" ")[1]
                self._virtual_world = vw
                if vw == "watertank":
                    self._watertank = watertank_simulation.Watertank(1000, [5, 5], [5], 0.5)
                    self._watertank.autoupdater_start(1)
                else:
                    pass
                
            elif command.startswith('VIRTUALWORLD_STATE'):
                self._virtual_world_state = str(self._watertank.get_water_level())
                return self._virtual_world_state
            
            elif command == 'SYNTHESIZING_RESULT':
                if(DEBUG):
                    print "[DBG]: SYNTHESIZING_RESULT: " + self._compiling_result
                return self._compiling_result
            
            elif command == 'READ_LEDS':
                try:
                    if self._led_reader == None:
                        if(DEBUG):
                            print "[DBG]: Initializing led reading."
                        self._load_led_reading_support()
                    self._led_state = self._led_reader.read_times(5)
                    if(DEBUG):
                        print "[DBG]: READ_LEDS: " + "".join(self._led_state)
                        
                    # This probably shouldn't be here. Ideally, the server by itself
                    # would every once in a while check the state of the LEDs and update
                    # the simulation's state automatically. For now, however, it will only
                    # check the state upon the client's request.
                    if self._virtual_world == "watertank":
                        first_pump = self._led_state[7]
                        second_pump = self._led_state[6]
                        if first_pump:
                            first_pump = 10
                        else:
                            first_pump = 0
                        if second_pump:
                            second_pump = 10
                        else:
                            second_pump = 0
                        self._watertank.set_input(0, first_pump)
                        self._watertank.set_input(1, second_pump)
                        
                    return "".join(self._led_state)
                except Exception as e:
                    traceback.print_exc()
                    return "ERROR: " + traceback.format_exc()

            # Otherwise we assume that the command is intended for the actual device handler
            # If it isn't, it throw an exception itself.

            if self._switches_reversed:
                if command.startswith("ChangeSwitch"):
                    command = command.replace(command[-1], str(9 - int(command[-1])))
            self._command_sender.send_command(command)
        except Exception as e:
            raise ExperimentErrors.SendingCommandFailureError(
                    "Error sending command to device: %s" % e
                )
