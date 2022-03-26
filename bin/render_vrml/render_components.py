#!/usr/bin/env python
############################################################################################
# Hellen-One: A 3D-component VRML rendering server script.
# Python 3.5+ is required.
# Dependencies: ModernGL, Pillow, Pyrr, NumPy, PyVRML97, Gzip
# (c) andreika <prometheus.pcb@gmail.com>
############################################################################################

import os, sys
import numpy as np
from pyrr import Matrix33,Matrix44,Vector3,Vector4,aabb
from vrml.vrml97 import parser,basenodes
from vrml import *
import moderngl as ModernGL
from moderngl_mesh import Mesh
from PIL import Image
import gzip

if (len(sys.argv) < 3):
    print ("Error! Please specify the VRML+image file names and DPI.")
    sys.exit(1)
fileName = sys.argv[1]
outFileName = sys.argv[2]
dpi = float(sys.argv[3])

curLocation = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


# uses ModernGL (OpenGL-based renderer with HW acceleration)
def render(model, outFileName, dpi):
    vertex_data = model.pack('vx vy vz cx cy cz nx ny nz')

    # Context creation
    ctx = ModernGL.create_standalone_context()

    # Shaders
    vertex_shader_source = open(os.path.join(curLocation, 'shader.vert')).read()
    fragment_shader_source = open(os.path.join(curLocation, 'shader.frag')).read()
    prog = ctx.program(vertex_shader = vertex_shader_source, fragment_shader = fragment_shader_source)

    # Matrices and Uniforms
    perspective = Matrix44.orthogonal_projection(model.aabb[0][0], model.aabb[1][0], model.aabb[0][1], model.aabb[1][1], 0.1, 1000.0)  # left,right,top,bottom,near,far
    lookat = Matrix44.look_at(
        (0,0,300),
        (0,0,0),
        (0.0, 1.0, 0.0),
    )

    mvp = perspective * lookat

    prog['LightDir'].value = (0.0, 0.0, -1.0)
    prog['AmbientColor'].value = (1.0, 1.0, 1.0, 0.25)
    prog['Mvp'].write(mvp.astype('f4').tobytes())

    # Vertex Buffer and Vertex Array
    vbo = ctx.buffer(vertex_data)
    vao = ctx.simple_vertex_array(prog, vbo, * ['in_vert', 'in_color', 'in_norm'])

    (width, height) = ((model.aabb[1][0:2] - model.aabb[0][0:2]) * dpi / 25.4 + 0.5).astype(int)
    print ("* Image size = " + str(width) + "x" + str(height))

    # Framebuffer
    fbo = ctx.framebuffer(ctx.renderbuffer((width, height)), ctx.depth_renderbuffer((width, height)),)

    # Rendering
    fbo.use()
    ctx.enable(ModernGL.DEPTH_TEST)
    ctx.clear(0.0, 0.0, 0.0, 0.0)
    vao.render()

    # Save the image using Pillow
    print ("* Saving to " + str(outFileName) + "...")
    data = fbo.read(components=4, alignment=1)
    img = Image.frombytes('RGBA', fbo.size, data, 'raw', 'RGBA', 0, -1)
    img.save(outFileName)

def addFaces(model, faces, mat, tm):
	offs = len(model.vert)
	# create an inverse transform matrix for normals
	tnm = Matrix33(tm)
	tnm = tnm.inverse.T
	# add vertices
	for i in range(0, len(faces.coord.point)):
		# position
		x = float(faces.coord.point[i][0])
		y = float(faces.coord.point[i][1])
		z = float(faces.coord.point[i][2])
		v = Vector4([x, y, z, 1.0])
		tv = tm * v
		# get normal (if present)
		try:
			(nx,ny,nz) = (faces.normal.vector[i][0:3])
			nv = Vector3([nx, ny, nz])
		except AttributeError:
			nv = Vector3([0,0,-1]) # default normal
		tnv = tnm * nv
		tnv.normalize()
		model.vert.append((tv.x, tv.y, tv.z))
		model.norm.append((tnv.x, tnv.y, tnv.z))
		model.color.append((mat.diffuseColor[0], mat.diffuseColor[1], mat.diffuseColor[2]))
		model.aabb = aabb.add_points(model.aabb, [tv.xyz])
	# add indices
	numFaces = int(len(faces.coordIndex) / 4)
	for i in range(0, numFaces):
		for ci in range(0, 3):
			idx = faces.coordIndex[i * 4 + ci]
			# indices are 1-based
			ind = int(idx + offs) + 1
			model.face.append((ind, ind, ind))

def processChildren(model, ch, tm):
	# iterate through all nodes
	for i,node in enumerate(ch):
		if (type(node) is basenodes.Group):
			processChildren(model, node.children, tm)
			continue
		if (type(node) is basenodes.Transform):
			transform = Matrix44(node.localMatrices().data[0].tolist()) if (node.localMatrices().data[0] is not None) else Matrix44.identity()
			# apply transform
			combinedTransform = tm * transform
			processChildren(model, node.children, combinedTransform)
			continue
		if (type(node) is basenodes.Shape and type(node.geometry) is basenodes.IndexedFaceSet):
			addFaces(model, node.geometry, node.appearance.material, tm)

############################################################################################

print ("* Reading " + fileName + "...")
if fileName.endswith('.gz'):
	print ("* Decompressing GZip...")
	data = gzip.open(fileName, "rt").read()
else:
	data = open(fileName).read()

print ("* Parsing the VRML data...")
parser = vrml97.parser.buildParser()
success, tags, next = parser.parse(data)
if (not success):
	print("VRML Parsing error: parsed %s characters of %s"%(next, len(data)))
	sys.exit(1)

print ("* Processing the data...")
model = Mesh([], [], [], [])
processChildren(model, tags[1].children, Matrix44.identity())

print ("* Num.Vertices = " + str(len(model.vert)) + " Num.Indices = " + str(len(model.face)))
print ("* AABB = " + str(model.aabb))

print ("* Rendering...")
render(model, outFileName, dpi)

print ("* Done!")
