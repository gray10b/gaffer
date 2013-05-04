//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
//  
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//  
//      * Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//  
//      * Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//  
//      * Neither the name of Image Engine Design nor the names of
//        any other contributors to this software may be used to endorse or
//        promote products derived from this software without specific prior
//        written permission.
//  
//  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
//  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
//  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
//  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
//  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
//  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
//  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
//  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
//  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
//  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//  
//////////////////////////////////////////////////////////////////////////

#include "IECore/AngleConversion.h"

#include "Gaffer/Transform2DPlug.h"

using namespace Imath;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( Transform2DPlug );

size_t Transform2DPlug::g_firstPlugIndex = 0;

Transform2DPlug::Transform2DPlug( const std::string &name, Direction direction, unsigned flags )
	:	CompoundPlug( name, direction, flags )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	
	addChild(
		new V2fPlug(
			"translate",
			direction,
			V2f( 0 ),
			V2f( limits<float>::min() ),
			V2f( limits<float>::max() ),			
			flags
		)
	);
		
	addChild(
		new FloatPlug(
			"rotate",
			direction,
			0.,
			limits<float>::min(),
			limits<float>::max(),
			flags
		)
	);
	
	addChild(
		new V2fPlug(
			"scale",
			direction,
			V2f( 1 ),
			V2f( limits<float>::min() ),
			V2f( limits<float>::max() ),			
			flags
		)
	);

	addChild(
		new V2fPlug(
			"pivot",
			direction,
			V2f( 0 ),
			V2f( limits<float>::min() ),
			V2f( limits<float>::max() ),			
			flags
		)
	);
	
}

Transform2DPlug::~Transform2DPlug()
{
}

bool Transform2DPlug::acceptsChild( const GraphComponent *potentialChild ) const
{
	return children().size() != 4;
}

PlugPtr Transform2DPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	return new Transform2DPlug( name, direction, getFlags() );
}

V2fPlug *Transform2DPlug::pivotPlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex+3 );
}

const V2fPlug *Transform2DPlug::pivotPlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex+3 );
}

V2fPlug *Transform2DPlug::translatePlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex );
}

const V2fPlug *Transform2DPlug::translatePlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex );
}

FloatPlug *Transform2DPlug::rotatePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex+1 );
}

const FloatPlug *Transform2DPlug::rotatePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex+1 );
}

V2fPlug *Transform2DPlug::scalePlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex+2 );
}

const V2fPlug *Transform2DPlug::scalePlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex+2 );
}

Imath::M33f Transform2DPlug::matrix() const
{
	M33f p;
	p.translate( pivotPlug()->getValue() );
	M33f t;
	t.translate( translatePlug()->getValue() );
	M33f r;
	r.rotate( IECore::degreesToRadians( rotatePlug()->getValue() ) );
	M33f s;
	s.scale( scalePlug()->getValue() );
	M33f pi;
	pi.translate( pivotPlug()->getValue()*Imath::V2f(-1.f) );
	M33f result = pi * s * r * t * p;

	return result;
}
