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
# Author: Jaime Irurzun <jaime.irurzun@gmail.com>
#

import voodoo.gen.coordinator.Address as cAddress
import voodoo.gen.generators.ClientSkel as ClientSkel
import voodoo.gen.protocols.protocols as Protocols

import voodoo.gen.exceptions.protocols.ProtocolErrors as ProtocolErrors

from voodoo.override import Override

class Address(cAddress.IpBasedAddress):

    def __init__(self, address):
        cAddress.IpBasedAddress.__init__(self, address)

    @Override(cAddress.IpBasedAddress)
    def create_client(self, methods):
        try:
            client_class = ClientSkel.factory(Protocols.InternetSocket, methods)
        except Exception as e:
            raise ProtocolErrors.ClientClassCreationError(("Client class creation exception: %s" % e), e)
        try:
            return client_class(hostname=self.ip_address, port=self.port)
        except Exception as e:
            raise ProtocolErrors.ClientInstanciationError(("Unable to instanciate the InternetSocket client: %s" % e),e)

    @Override(cAddress.IpBasedAddress)
    def get_protocol(self):
        return Protocols.InternetSocket

    @Override(cAddress.IpBasedAddress)
    def __cmp__(self, other):
        return cAddress.IpBasedAddress._compare(self, other)

    @Override(cAddress.IpBasedAddress)
    def __eq__(self, other):
        return self.__cmp__(other) == 0

