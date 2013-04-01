##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
#  
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#  
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#  
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#  
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#  
##########################################################################

from __future__ import with_statement

import IECore

import Gaffer
import GafferUI

class NodeGraph( GafferUI.EditorWidget ) :

	def __init__( self, scriptNode, **kw ) :
				
		self.__gadgetWidget = GafferUI.GadgetWidget(
			bufferOptions = set( [
				GafferUI.GLWidget.BufferOptions.Double,
			] ),
		)
		
		GafferUI.EditorWidget.__init__( self, self.__gadgetWidget, scriptNode, **kw )
		
		graphGadget = GafferUI.GraphGadget( self.scriptNode() )
		self.__rootChangedConnection = graphGadget.rootChangedSignal().connect( Gaffer.WeakMethod( self.__rootChanged ) )
		
		self.__gadgetWidget.getViewportGadget().setChild( graphGadget )
		self.__frame()		

		self.__buttonPressConnection = self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		self.__keyPressConnection = self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )
		self.__buttonDoubleClickConnection = self.buttonDoubleClickSignal().connect( Gaffer.WeakMethod( self.__buttonDoubleClick ) )
		
	## Returns the internal GadgetWidget holding the GraphGadget.	
	def graphGadgetWidget( self ) :
	
		return self.__gadgetWidget

	## Returns the internal Gadget used to draw the graph. This may be
	# modified directly to set up appropriate filters etc. This is just
	# a convenience method returning graphGadgetWidget().getViewportGadget().getChild().
	def graphGadget( self ) :
	
		return self.graphGadgetWidget().getViewportGadget().getChild()
	
	def getTitle( self ) :
	
		result = IECore.CamelCase.toSpaced( self.__class__.__name__ )
	
		root = self.graphGadget().getRoot()
		if not root.isSame( self.scriptNode() ) :
			result += " : " + root.relativeName( self.scriptNode() )
		
		return result
		
	__nodeContextMenuSignal = Gaffer.Signal3()
	## Returns a signal which is emitted to create a context menu for a
	# node in the graph. Slots may connect to this signal to edit the
	# menu definition on the fly - the signature for the signal is
	# ( nodeGraph, node, menuDefinition ) and the menu definition should just be
	# edited in place. Typically you would add slots to this signal
	# as part of a startup script.
	@classmethod
	def nodeContextMenuSignal( cls ) :
	
		return cls.__nodeContextMenuSignal
	
	__nodeDoubleClickSignal = Gaffer.Signal2()
	## Returns a signal which is emitted whenever a node is double clicked.
	# Slots should have the signature ( nodeGraph, node ).
	@classmethod
	def nodeDoubleClickSignal( cls ) :
	
		return cls.__nodeDoubleClickSignal
	
	## Ensures that the specified node has a visible NodeGraph viewing
	# it, and returns that editor.
	## \todo Consider how this relates to the todo items in NodeEditor.acquire().
	@classmethod
	def acquire( cls, rootNode ) :
	
		if isinstance( rootNode, Gaffer.ScriptNode ) :
			script = rootNode
		else :
			script = rootNode.scriptNode()
			
		scriptWindow = GafferUI.ScriptWindow.acquire( script )
		tabbedContainer = None
		for editor in scriptWindow.getLayout().editors( type = GafferUI.NodeGraph ) :
			if rootNode.isSame( editor.graphGadget().getRoot() ) :
				editor.parent().setCurrent( editor )
				return editor
					
		editor = NodeGraph( script )
		editor.graphGadget().setRoot( rootNode )
		scriptWindow.getLayout().addEditor( editor )
		
		return editor
		
	def __repr__( self ) :

		return "GafferUI.NodeGraph( scriptNode )"	

	def __buttonPress( self, widget, event ) :
				
		if event.buttons & GafferUI.ButtonEvent.Buttons.Right :
						
			# right click - display either the node creation popup menu
			# or a menu specific to the node under the mouse if possible.
			
			menuDefinition = GafferUI.NodeMenu.definition()
			
			nodeGadget = self.__nodeGadgetAt( event.line.p1 )				
			if nodeGadget :
				nodeMenuDefinition = IECore.MenuDefinition()
				self.nodeContextMenuSignal()( self, nodeGadget.node(), nodeMenuDefinition )
				if len( nodeMenuDefinition.items() ) :
					menuDefinition = nodeMenuDefinition
		
			self.__m = GafferUI.Menu( menuDefinition )
			self.__m.popup( self )
						
			return True
	
		return False
	
	def __nodeGadgetAt( self, position ) :
	
		viewport = self.__gadgetWidget.getViewportGadget()
		line = viewport.rasterToGadgetSpace( IECore.V2f( position.x, position.y ) )
		return self.graphGadget().nodeGadgetAt( line )
	
	def __keyPress( self, widget, event ) :
	
		if event.key == "F" :
			self.__frame()
			return True
		## \todo This cursor key navigation might not make sense for all applications,
		# so we should move it into BoxUI and load it in a config file that the gui app uses.
		# I think this implies that every Widget.*Signal() method should have a
		# Widget.static*Signal() method to allow global handlers to be registered by widget type.
		# We already have a mix of static/nonstatic signals for menus, so that might make a nice
		# generalisation.
		elif event.key == "Down" :
			selection = self.scriptNode().selection()
			if selection.size() and isinstance( selection[0], Gaffer.Box ) :
				self.graphGadget().setRoot( selection[0] )
				self.__frame()
				return True
		elif event.key == "Up" :
			root = self.graphGadget().getRoot()
			if isinstance( root, Gaffer.Box ) :
				self.graphGadget().setRoot( root.parent() )
				return True
				
		return False
		
	def __frame( self ) :
	
		graphGadget = self.graphGadget()
		
		# get the bounds of the selected nodes
		scriptNode = self.scriptNode()
		selection = scriptNode.selection()
		bound = IECore.Box3f()
		for node in selection :
			nodeGadget = graphGadget.nodeGadget( node )
			if nodeGadget :
				bound.extendBy( nodeGadget.transformedBound( graphGadget ) )
		
		# if there were no nodes selected then use the bound of the whole
		# graph.		
		if bound.isEmpty() :
			bound = graphGadget.bound()
			
		# if there's still nothing then an arbitrary area in the centre of the world
		if bound.isEmpty() :
			bound = IECore.Box3f( IECore.V3f( -10, -10, 0 ), IECore.V3f( 10, 10, 0 ) )
			
		# pad it a little bit so
		# it sits nicer in the frame
		bound.min -= IECore.V3f( 5, 5, 0 )
		bound.max += IECore.V3f( 5, 5, 0 )
				
		# now adjust the bounds so that we don't zoom in further than we want to
		boundSize = bound.size()
		widgetSize = IECore.V3f( self._qtWidget().width(), self._qtWidget().height(), 0 )
		pixelsPerUnit = widgetSize / boundSize
		adjustedPixelsPerUnit = min( pixelsPerUnit.x, pixelsPerUnit.y, 10 )
		newBoundSize = widgetSize / adjustedPixelsPerUnit
		boundCenter = bound.center()
		bound.min = boundCenter - newBoundSize / 2.0
		bound.max = boundCenter + newBoundSize / 2.0
			
		self.__gadgetWidget.getViewportGadget().frame( bound )
	
	def __buttonDoubleClick( self, widget, event ) :
	
		nodeGadget = self.__nodeGadgetAt( event.line.p1 )				
		if nodeGadget is not None :
			return self.nodeDoubleClickSignal()( self, nodeGadget.node() )
	
	def __rootChanged( self, graphGadget ) :
	
		if graphGadget.getRoot().isSame( self.scriptNode() ) :
			self.__rootNameChangedConnection = None
			self.__rootParentChangedConnection = None
		else :
			self.__rootNameChangedConnection = graphGadget.getRoot().nameChangedSignal().connect( Gaffer.WeakMethod( self.__rootNameChanged ) )
			self.__rootParentChangedConnection = graphGadget.getRoot().parentChangedSignal().connect( Gaffer.WeakMethod( self.__rootParentChanged ) )
			
		self.titleChangedSignal()( self )
		
	def __rootNameChanged( self, root ) :
	
		self.titleChangedSignal()( self )
		
	def __rootParentChanged( self, root, oldParent ) :
	
		# root has been deleted
		## \todo I'm not sure if we should be responsible for removing ourselves or not.
		# Perhaps we should just signal that we're not valid in some way and the CompoundEditor should
		# remove us? Consider how this relates to NodeEditor.__deleteWindow() too.
		self.parent().removeChild( self )
	
GafferUI.EditorWidget.registerType( "NodeGraph", NodeGraph )