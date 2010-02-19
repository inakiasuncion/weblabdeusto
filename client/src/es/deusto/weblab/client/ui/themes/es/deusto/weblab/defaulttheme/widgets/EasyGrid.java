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
* Author: FILLME
*
*/

package es.deusto.weblab.client.ui.themes.es.deusto.weblab.defaulttheme.widgets;

import java.util.ArrayList;

import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.Widget;


/**
 * EasyGrid is meant to provide the same features as a Grid, from which it inherits,
 * but it is meant to be used from UIBinder. Hence, the number of rows and columns can be 
 * set through its rows and cols properties (rather than through the ctor), and the 
 * default add() method is supported, so that its widgets can be specified from XML and
 * setWidget() is no longer required. Widgets are arranged in the table in order (as they
 * appear in the XML), from left to right and from top to bottom.
 */
public class EasyGrid extends Grid {
	
	/**
	 * List that will store every widget added to the grid.
	 */
	private final ArrayList<Widget> widgets = new ArrayList<Widget>();
	private int cols = -1;
	private int rows = -1;
	
	/**
	 * Creates or resizes the table. Cols and Rows need to have been set already. Every
	 * internally stored widget is assigned a cell in order, from left to right and top to bottom.
	 */
	private void createTable()
	{
		System.out.println("Creating table.");
		
		this.resize(rows, cols);
		
		int widgetsSet = 0;
		for(int j = 0; j < rows && widgetsSet < widgets.size(); j++) {
			for(int i = 0; i < cols && widgetsSet < widgets.size(); i++) {
				this.setWidget(j, i, widgets.get(widgetsSet));
				widgetsSet++;
			}
		}
	}

	/**
	 * Constructs an EasyGrid.
	 */
	public EasyGrid() {
		this.resize(4, 4);
		Label label = new Label("TESTING EASYGRID");
		System.out.println("Constructing EASYGRID");
		this.setWidget(0, 0, label);
	}
	
	/**
	 * Sets the number of columns of the table.
	 * @param cols Number of columns.
	 */
	public void setCols(int cols) {
		System.out.println("Settings cols.");
		this.cols = cols;
		if(rows != -1 && cols != -1)
			createTable();
	}
	
	/**
	 * Sets the number of rows of the table.
	 * @param rows Number of rows.
	 */
	public void setRows(int rows) {
		System.out.println("Settings rows.");
		this.rows = rows;
		if(rows != -1 && cols != -1)
			createTable();
	}
	
	/**
	 * Adds a widget to the table. The EasyGrid stores widgets internally without
	 * actually displaying them, until both the cols and rows numbers have been
	 * set.
	 */
	@Override
	public void add(Widget widget)
	{
		System.out.println("Adding widget to the internal list.");
		widgets.add(widget);
	}

}
