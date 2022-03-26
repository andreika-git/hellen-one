#!/usr/bin/env python
############################################################################################
# Hellen-One: A board rendering server script.
# Python 3.5+ is required.
# Dependencies: Pillow
# (c) andreika <prometheus.pcb@gmail.com>
############################################################################################

import os, sys
from PIL import Image

if (len(sys.argv) < 6):
	print ("* Error! Please specify correct arguments to run this script!")
	sys.exit(1)

pcbImgFile = sys.argv[1]
outlineImgFile = sys.argv[2]
compImgFile = sys.argv[3]
boardImgFile = sys.argv[4]
compImgOffset = [int(n) for n in sys.argv[5].split(",")]

class ImageObject:
	width = 0
	height = 0
	data = []

def getPixel(img, x, y):
	if (x < 0 or y < 0 or x >= img.width or y >= img.height):
		return [0, 0, 0, 0]
	return img.data[x, y]

def createBoardImg(pcbImg, outlineImg, compImg, compImgOffset):
	width = max([pcbImg.width, outlineImg.width, compImg.width])
	height = max([pcbImg.height, outlineImg.height, compImg.height])
	boardImg = Image.new('RGBA', (width, height))

	pcbOffY = -(outlineImg.height - pcbImg.height) if (pcbImg.height < outlineImg.height) else 0
	# Blit the pcbImg using the outlineImg mask and add compImg.
	# We cannot use PNG.bitblt() for that
	for y in range(0, boardImg.height):
		for x in range(0, boardImg.width):
			bPixel = getPixel(pcbImg, x, y + pcbOffY)
			cPixel = getPixel(compImg, x + compImgOffset[0], y + compImgOffset[1])
			a = float(cPixel[3]) / 255.0
			na = 1.0 - a
			pr = int(na * bPixel[0] + a * cPixel[0])
			pg = int(na * bPixel[1] + a * cPixel[1])
			pb = int(na * bPixel[2] + a * cPixel[2])
			pa = int(na * getPixel(outlineImg, x, y)[0] + a * 255)
			boardImg.putpixel((x, y), (pr, pg, pb, pa))
	return boardImg

def loadImage(fileName):
	pimg = Image.open(fileName).convert("RGBA")
	img = ImageObject()
	img.data = pimg.load()
	img.width = pimg.size[0]
	img.height = pimg.size[1]
	return img

print ("* Reading the pcb image...")
pcbImg = loadImage(pcbImgFile)
print ("* Reading the components image with offset (" + str(compImgOffset[0]) + "," + str(compImgOffset[1]) + ")...")
compImg = loadImage(compImgFile)
print ("* Reading the outline image...")
outlineImg = loadImage(outlineImgFile)

print ("* Creating the final board image...")
boardImg = createBoardImg(pcbImg, outlineImg, compImg, compImgOffset)
print ("* Saving the board image...")
boardImg.save(boardImgFile)

print ("* Done! Exiting...")
