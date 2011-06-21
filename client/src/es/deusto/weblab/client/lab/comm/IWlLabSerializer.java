/*
* Copyright (C) 2005-2009 University of Deusto
* All rights reserved.
*
* This software is licensed as described in the file COPYING, which
* you should have received as part of this distribution.
*
* This software consists of contributions made by many individuals, 
* listed below:
*
* Author: Pablo Orduña <pablo@ordunya.com>
*         Luis Rodriguez <luis.rodriguez@opendeusto.es>
*
*/ 
package es.deusto.weblab.client.lab.comm;

import es.deusto.weblab.client.comm.IWlCommonSerializer;
import es.deusto.weblab.client.comm.exceptions.SerializationException;
import es.deusto.weblab.client.comm.exceptions.WlServerException;
import es.deusto.weblab.client.comm.exceptions.core.SessionNotFoundException;
import es.deusto.weblab.client.comm.exceptions.core.UserProcessingException;
import es.deusto.weblab.client.dto.SessionID;
import es.deusto.weblab.client.dto.experiments.AsyncRequestStatus;
import es.deusto.weblab.client.dto.experiments.Command;
import es.deusto.weblab.client.dto.experiments.ExperimentAllowed;
import es.deusto.weblab.client.dto.experiments.ExperimentID;
import es.deusto.weblab.client.dto.experiments.ResponseCommand;
import es.deusto.weblab.client.dto.reservations.ReservationStatus;
import es.deusto.weblab.client.lab.comm.exceptions.NoCurrentReservationException;
import es.deusto.weblab.client.lab.comm.exceptions.UnknownExperimentIdException;

public interface IWlLabSerializer extends IWlCommonSerializer{
	
	ResponseCommand parseSendAsyncCommandResponse(String responseText)
	throws SerializationException,  SessionNotFoundException, NoCurrentReservationException, UserProcessingException, WlServerException;

	ExperimentAllowed [] parseListExperimentsResponse(String responseText) 
		throws SerializationException, SessionNotFoundException, UserProcessingException, WlServerException;
	
	ReservationStatus parseReserveExperimentResponse(String responseText) 
		throws SerializationException, SessionNotFoundException, UnknownExperimentIdException, UserProcessingException, WlServerException;
	
	void parseFinishedExperimentResponse(String responseText) 
		throws SerializationException, SessionNotFoundException, NoCurrentReservationException, UserProcessingException, WlServerException;

	ReservationStatus parseGetReservationStatusResponse(String responseText) 
		throws SerializationException, SessionNotFoundException, NoCurrentReservationException, UserProcessingException, WlServerException;
	
	ResponseCommand parseSendCommandResponse(String responseText) 
		throws SerializationException, SessionNotFoundException, NoCurrentReservationException, UserProcessingException, WlServerException;
	
	void parsePollResponse(String responseText) 
		throws SerializationException, SessionNotFoundException, NoCurrentReservationException, UserProcessingException, WlServerException;

	ResponseCommand parseSendFileResponse(String responseText)
		throws SerializationException, SessionNotFoundException, NoCurrentReservationException, UserProcessingException, WlServerException;
	
	AsyncRequestStatus [] parseCheckAsyncCommandStatusResponse(String responseText) 
		throws SerializationException, SessionNotFoundException, NoCurrentReservationException, UserProcessingException, WlServerException;
	
	String serializeGetReservationStatusRequest(SessionID sessionId) throws SerializationException;
	String serializeListExperimentsRequest(SessionID sessionId) throws SerializationException;
	String serializePollRequest(SessionID sessionId) throws SerializationException;
	String serializeReserveExperimentRequest(SessionID sessionId, ExperimentID experimentId) throws SerializationException;
	String serializeSendCommandRequest(SessionID sessionId, Command command) throws SerializationException;
	String serializeSendAsyncCommandRequest(SessionID sessionId, Command command) throws SerializationException;
	String serializeFinishedExperimentRequest(SessionID sessionId) throws SerializationException;
	String serializeCheckAsyncCommandStatusRequest(SessionID sessionId, String [] requestIdentifiers) throws SerializationException;
}
