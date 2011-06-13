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
*
*/ 
package es.deusto.weblab.client.comm;

import com.google.gwt.http.client.Request;
import com.google.gwt.http.client.RequestCallback;
import com.google.gwt.http.client.Response;

import es.deusto.weblab.client.comm.callbacks.IWlAsyncCallback;
import es.deusto.weblab.client.comm.exceptions.CommunicationException;
import es.deusto.weblab.client.comm.exceptions.ServerException;


/**
 * Callback to be invoked whenever a request finishes. Holds an internal
 * IWlAsyncCallback, which will be invoked if an error occurs. 
 * 
 * Though this callback does apparently have methods to support both success and error 
 * notification, receiving a response successfully does not necessarily mean that the
 * request succeeded. Hence the need for the aforementioned callback within this
 * callback.
 */
abstract public class WlRequestCallback implements RequestCallback{

	private final IWlAsyncCallback callback;
	
	/**
	 * Constructs the WlRequestCallback.
	 * @param callback IWlAsyncCallback to be invoked by the WlRequestCallback if
	 * an error occurs. For instance, if the server returns an error code, or if the
	 * request fails.
	 */
	public WlRequestCallback(IWlAsyncCallback callback){
		this.callback = callback;
	}
	
	@Override
	public void onError(Request request, Throwable exception) {
		this.callback.onFailure(new CommunicationException(exception.getMessage(), exception));
	}

	@Override
	public void onResponseReceived(Request request, Response response) {
		final int stateCode = response.getStatusCode();
		// 5XX and 4XX are server errors
		// 500 might be returned when a SOAP-Fault is raised, so we're not going to filter it
		final int firstNumber = (stateCode / 100) % 1000;
		if(firstNumber == 4 || (firstNumber == 5 && stateCode != 500)){
			this.callback.onFailure(new ServerException("Couldn't contact with the server: " + response.getStatusText()));
		}else{
			this.onSuccessResponseReceived(response.getText());
		}
	}

	public abstract void onSuccessResponseReceived(String message);
}
