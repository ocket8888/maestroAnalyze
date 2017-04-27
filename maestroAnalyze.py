#!/usr/bin/env python3

import argparse
import datetime as dt
from math import log, sqrt
from sys import stdin, stdout, stderr


#Figure out where the data's coming from
parser = argparse.ArgumentParser(description="Displays data exported in ASCII format from Maestro software.")

parser.add_argument("FILE", type=str, nargs='?', default=None, help="The name of the file to read from. If not given, reads from stdin.")
parser.add_argument("-t", dest='text', default=False, action="store_true", help="operates in text-mode, outputting some information to stdout and exiting.")
args=parser.parse_args()

if args.FILE:
	infile=open(args.FILE)
else:
	infile=stdin

contents = infile.read().strip().split("\n")


class ROI:
	"""Holds information about a region of interest"""
	def __init__(self, start, end):
		self.start = start
		self.end = end
		self.containedSpectrum = data[start:end+1:]
		self.background = self.calculateBackground(self.start, self.end, self.containedSpectrum)
		self.NetArea, self.NetAreaError = self.calculateNetArea(self.start, self.end, self.containedSpectrum)
		self.GrossArea = sum(self.containedSpectrum)
		self.FWHM = self.calculateFWHM(start, end, self.containedSpectrum)

	def calculateBackground(self, start, end, spectrum=None):
		if spectrum == None:
			spectrum = data[start:end+1:]

		return (sum(spectrum[:3:])+sum(spectrum[len(spectrum)-4::]))*(len(spectrum)+1)/6

	def calculateNetArea(self, start, end, spectrum=None):
		if spectrum == None:
			spectrum = data[start:end+1:]

		adjustedWidth = (end - start - 5)/(end - start + 1)

		adjustedGross = sum(spectrum[3:len(spectrum)-3:])
		background = self.calculateBackground(start, end, spectrum)
		netError = sqrt(adjustedGross + (background * adjustedWidth * (end-start-5)/6))

		return adjustedGross - (background * adjustedWidth), netError

	def calculateFWHM(self, start, end, spectrum=None):
		if spectrum == None:
			spectrum = data[start:end+1:]

		parity = 1 if len(spectrum)%2 == 1 else 0

		maximum = max(spectrum)
		middle = len(spectrum)//2 + parity - 1

		leftbin, rightbin = 0, middle + 1
		for i in range(1, middle):
			if abs(spectrum[i] - (maximum/2)) < abs(spectrum[leftbin] - (maximum/2)):
				leftbin = i
			if abs(spectrum[middle+i] - (maximum/2)) < abs(spectrum[rightbin] - (maximum/2)):
				rightbin = i

		return rightbin - leftbin


#read the data into its fields
fields = dict()
currentField = ""
for line in contents:
	if line[0] == '$':
		currentField = line[1:len(line)-1:]
		fields[currentField]=list()
		continue
	fields[currentField].append(line)

#parse the easy fields
sample_description = fields["SPEC_ID"][0]
measurement_time = fields["MEAS_TIM"][0].split(" ")
measurement_time = {"live": int(measurement_time[0]), "real": int(measurement_time[1])}
date_time = dt.datetime.strptime(fields["DATE_MEA"][0], "%m/%d/%Y %H:%M:%S")

#parse the collected data
data = fields["DATA"]
minMax = [int(x) for x in data.pop(0).split(" ")]
data = [int(counts.strip()) for counts in data ]
countsMax = max(data)

#check for ROI's and read them in if applicable
roi = fields["ROI"]
roiNum = int(roi.pop(0))
regions = list()
for region in roi:
	bounds = region.split(" ")
	regions.append(ROI(int(bounds[0]), int(bounds[1])))

if args.text:
	print(sample_description)
	print("Measurements taken starting at "+str(date_time)+" for "+repr(measurement_time["real"])+" s ("+repr(measurement_time["live"])+" s 'live time')")
	print("Regions of Interest:")
	for r in regions:
		print("------------------------------------------")
		print("Channels "+repr(r.start)+" to "+repr(r.end))
		print("Net Area: "+repr(r.NetArea)+" +/- "+repr(r.NetAreaError))
		print("GrossArea: "+repr(r.GrossArea))
		print("FWHM: "+repr(r.FWHM))
		print("Peak Count: "+repr(r.containedSpectrum[len(r.containedSpectrum)//2 + len(r.containedSpectrum)%2 - 1]))
		print("Max Count: "+repr(max(r.containedSpectrum)))
	print("------------------------------------------")
	exit()

#start the display
import pygame
from pygame.locals import *
if not pygame.font:
	print("Warning, fonts disabled")

pygame.init()
displayInfo = pygame.display.Info()

screenSize = (displayInfo.current_w, displayInfo.current_h)
font_size = int(0.013*screenSize[1])
white = (255, 255, 255)
black = (0, 0, 0)
limeGreen = (50, 205, 50)
paleBlue = (145, 163, 210)
paleTurquoise = (175, 255, 222)

screen = pygame.display.set_mode(screenSize)
screen.fill(white)
pygame.display.update()

#Currently only use this button to switch between linear scale and (broken) log scale
#useful for other things though, so it's a class
class Button:
	def __init__(self, surface, color, x, y, width, height, text, text_color):
		self.x = x
		self.y = y
		self.height = height
		self.width = width
		self.color = color
		self.text_color = text_color
		self.parentSurface = surface
		self.text = text
		self.buttonSurface = self.draw_button()
		self.write_text()
		self.rect = pygame.Rect(x,y, width, height)

	def write_text(self):
		myFont = pygame.font.SysFont("Calibri", font_size)
		myText = myFont.render(self.text, 1, self.text_color)
		self.buttonSurface.blit(myText, ((self.width//2) - myText.get_width()//2, (self.height//2) - myText.get_height()//2))

	def draw_button(self):
		surface = pygame.Surface((self.width, self.height))
		surface.fill(self.color)
		pygame.draw.rect(surface, (190,190,190), (1,1,self.width-1,self.height-1), 1)
		self.parentSurface.blit(surface, (self.x, self.y))
		return surface

	def repaint(self, newText):
		if newText == None:
			newText = self.text
		self.buttonSurface.fill(self.color)
		pygame.draw.rect(self.buttonSurface, (190,190,190), (1,1,self.width-1,self.height-1), 1)
		font_size = self.width//len(newText)+5
		myFont = pygame.font.SysFont("Calibri", font_size)
		myText = myFont.render(newText, 1, self.text_color)
		self.buttonSurface.blit(myText, ((self.width//2) - myText.get_width()//2, (self.height//2) - myText.get_height()//2))
		self.text = newText
		self.parentSurface.blit(self.buttonSurface, (self.x, self.y))


	def pressed(self, mouse):
		if mouse[0] > self.rect.topleft[0]:
			if mouse[1] > self.rect.topleft[1]:
				if mouse[0] < self.rect.bottomright[0]:
					if mouse[1] < self.rect.bottomright[1]:
						return True
		return False

class Infobox:
	"""Displays info about a selected region"""
	def __init__(self, bkgrndColor, region=None):
		self.bkgrndColor = bkgrndColor
		self.NetArea = 0
		self.NetAreaError = 0
		self.FWHM = 0
		self.NetCounts = 0
		self.BinRange = None
		self.PeakCount = 0
		self.MaxCount = 0
		self.surface = None
		self.region = region
		if region:
			self.setRegion(region)

	def setRegion(self, reg):
		self.region = reg
		self.NetArea = reg.NetArea
		self.NetAreaError = reg.NetAreaError
		self.BinRange = (reg.start, reg.end)
		self.GrossArea = reg.GrossArea
		self.PeakCount = reg.containedSpectrum[len(reg.containedSpectrum)//2 + len(reg.containedSpectrum)%2 - 1]
		self.MaxCount = max(reg.containedSpectrum)
		self.FWHM = reg.FWHM
		self.paint()

	def clear(self):
		self.region = None

	def paint(self):
		self.surface = pygame.Surface((screenSize[0] - 420, 10+2*font_size)) #dank
		self.surface.fill(self.bkgrndColor)
		myFont = pygame.font.SysFont("Calibri", font_size)
		binText = "Channel Range: "
		areaText = "Net Area: "
		grossText = "Gross Area: "
		peakText = "Center Count: "
		maxText = "Maximum Count: "
		fwhmText = "FWHM: "
		if self.region:
			binText += "["+repr(self.BinRange[0])+", "+repr(self.BinRange[1])+"]"

			netAreaBase = repr(self.NetArea)
			if len(netAreaBase) > 6:
				netAreaBase = netAreaBase[:6:]

			netAreaError = repr(self.NetAreaError)
			if len(netAreaError) > 6:
				netAreaError = netAreaError[:6:]
			areaText += netAreaBase+" +/-"+netAreaError
			grossText += repr(self.GrossArea)
			peakText += repr(self.PeakCount)
			maxText += repr(self.MaxCount)
			fwhmText += repr(self.FWHM)
		else:
			binText += "N/A"
			areaText += "N/A"
			grossText += "N/A"
			peakText += "N/A"
			maxText += "N/A"
			fwhmText += "N/A"
		binText = myFont.render(binText, 1, black)
		areaText = myFont.render(areaText, 1, black)
		grossText = myFont.render(grossText, 1, black)
		peakText = myFont.render(peakText, 1, black)
		maxText = myFont.render(maxText, 1, black)
		fwhmText = myFont.render(fwhmText, 1, black)

		self.surface.blit(binText, (5, 5))
		self.surface.blit(areaText, (5, 10+font_size))
		self.surface.blit(grossText, (11*font_size+20, 5))
		self.surface.blit(peakText, (11*font_size+20, 10+font_size))
		self.surface.blit(maxText, (18*font_size+40, 5))
		self.surface.blit(fwhmText, (18*font_size+40, 10+font_size))

		

#define the graph's draw area
graphOffset = (50, 15+2*font_size) #(left offset, top offset)
graphSize = (screenSize[0]-2*graphOffset[0], int(screenSize[1]*(1-1/50))-graphOffset[1])
graphArea = pygame.Surface(graphSize)
screen.blit(graphArea, graphOffset)

#This function draws an arbitrary spectrum
def drawSpectrum(spectrum, boundaries):
	binNumber = 0
	specMax =  max(spectrum)
	graphSurface = pygame.Surface(graphSize)
	graphSurface.fill(white)
	for Bin in spectrum:
		binColor = ( 255 - int((specMax - Bin)*(255.0/specMax)), 32, int((specMax - Bin)*(255.0/specMax)))
		for region in regions:
			if binNumber + boundaries[0] in range(region.start, region.end+1):
				binColor = limeGreen
				break
		pygame.draw.rect(graphSurface, binColor, (int(binNumber*(graphSize[0]/len(spectrum))), graphSize[1]-(Bin*graphSize[1]//specMax), (graphSize[0]/len(spectrum))-1, Bin*graphSize[1]//specMax))
		binNumber += 1
	return graphSurface

#This function toggles linear and logarithmic displays, for button use
def linLogToggle(linear, spectrum, boundary):
	if linear:
		return drawSpectrum(spectrum, boundary)
	return drawSpectrum([log(count + 1, 10) for count in spectrum], boundary) #adds 1 to avoid exploding on 0 count bins

#Checks if a mouse click happens inside a surface
def inObject(mouse, obj):
	objRect = obj.get_rect() #more like get rekt lol
	if mouse[0] > objRect.topleft[0]:
		if mouse[1] > objRect.topleft[1]:
			if mouse[0] < objRect.bottomright[0]:
				if mouse[1] < objRect.bottomright[1]:
					return True
	return False

def selectBins(dragStart, dragEnd, spec):
	leftside, rightside = min((dragStart, dragEnd)), max((dragStart, dragEnd))
	draggedSize = (rightside - leftside, graphSize[1])
	draggedSurface = pygame.Surface(draggedSize)
	draggedSurface.set_alpha(100)
	draggedSurface.fill(paleBlue)
	draggedBins = (leftside*len(spec)//graphSize[0], rightside*len(spec)//graphSize[0])
	return (draggedSurface, leftside, draggedBins)

#Yes this is basically just a list comprehension, yes doing it this way is probably slower
#No, I don't care. It's way easier to read this way.
def calculateSelectableRegions(boundaries):
	canSelect = list()
	for region in regions:
		if region.start in range(boundaries[0], boundaries[1]+1) and region.end in range(boundaries[0], boundaries[1]+1):
			canSelect.append(region)
	return canSelect

def selectROI(currentROI, boundaries, spectrumSize, selectNext=False):
	if len(selectableRegions) == 0:
		return False, None

	if selectNext:
		if currentROI == None:
			newlySelectedROI = 0
		else:
			newlySelectedROI = (currentROI + 1) % len(selectableRegions)
	else:
		if currentROI == None or currentROI == 0:
			newlySelectedROI = len(selectableRegions) - 1
		else:
			newlySelectedROI = currentROI -1

	regionData = selectableRegions[newlySelectedROI]

	draggedSize = ((regionData.end - regionData.start+1)*graphSize[0]//spectrumSize, graphSize[1])
	draggedSurface = pygame.Surface(draggedSize)
	draggedSurface.set_alpha(100)
	draggedSurface.fill(paleTurquoise)
	
	leftside = (regionData.start - boundaries[0])*graphSize[0]//spectrumSize

	return (draggedSurface, leftside, (regionData.start, regionData.end)), newlySelectedROI




graph = drawSpectrum(data, minMax).convert()
buttonText = "Log Scale"
linLogButton = Button(screen, limeGreen, 15, 5, 100, 2*font_size+10, buttonText, black)
infobox = Infobox(white)

currentSpectrum = data #always preserves linear scale, so we don't lose resolution
currentBounds = minMax
dragging = False
dragged = False
unzoom = False
selectedROI = None
selectableRegions = regions


#main loop
while True:
	screen.fill(white)
	for event in pygame.event.get():

		#handle window close (fucking sort of)
		if event.type == pygame.QUIT:
			pygame.display.quit()
			pygame.quit()
			exit()

		#handle mouse clicks
		elif event.type == MOUSEBUTTONDOWN:
			mousePos = pygame.mouse.get_pos()

			#check for user toggling linear and log scales
			if linLogButton.pressed(mousePos):
				if buttonText == "Linear Scale":
					graph = linLogToggle(True, currentSpectrum, currentBounds).convert()
					buttonText = "Log Scale"
				else:
					graph = linLogToggle(False, currentSpectrum, currentBounds).convert()
					buttonText = "Linear Scale"

			#if an area is drag selected, check if the user pushes the "Zoom" button
			elif dragged and zoomButton.pressed(pygame.mouse.get_pos()):
				buttonText = "Log Scale"
				currentBounds = (currentBounds[0] + dragged[2][0], currentBounds[0] + dragged[2][1])
				currentSpectrum = currentSpectrum[dragged[2][0]:dragged[2][1]+1:]
				dragged = False
				selectedROI = None
				infobox.clear()
				selectableRegions = calculateSelectableRegions(currentBounds)
				graph = drawSpectrum(currentSpectrum, currentBounds).convert()
				unzoom = True
				unzoomButton = Button(screen, paleBlue, screenSize[0]-240, 5, 100, 2*font_size+10, "Zoom Out", black)

			#if spectrum is zoomed, check if the user pushes the "Zoom Out" button
			elif unzoom and unzoomButton.pressed(pygame.mouse.get_pos()):
				currentSpectrum = data
				currentBounds = minMax
				selectableRegions = regions
				infobox.clear()
				unzoom = False
				dragged = False
				graph = drawSpectrum(currentSpectrum, currentBounds).convert()
				buttonText = "Log Scale"

			#if the user clicks in the graph area, start a drag select
			elif inObject(mousePos, graphArea):
				dragged = False
				selectedROI = None
				draggingX, draggingY = mousePos
				draggingX -= graphOffset[0]
				dragging = (draggingX, draggingY)

		#handles when the mousebutton is released (currently only use is for ending a drag-select)
		elif event.type == MOUSEBUTTONUP and dragging:
			mousePos = pygame.mouse.get_pos()
			dragged = selectBins(dragging[0], mousePos[0] - graphOffset[0], currentSpectrum)
			dragging = False
			zoomButton = Button(screen, paleBlue, screenSize[0] - 120, 5, 100, 2*font_size+10, "Zoom", black)
			infobox.setRegion(ROI(currentBounds[0]+dragged[2][0], currentBounds[0]+dragged[2][1]))

		#handle key presses
		elif event.type == KEYDOWN:
			keys = pygame.key.get_pressed()
			if keys[K_RIGHT]:
				dragging = False
				dragged, selectedROI = selectROI(selectedROI, currentBounds, len(currentSpectrum), selectNext=True)
				infobox.setRegion(selectableRegions[selectedROI])
			elif keys[K_LEFT]:
				dragging = False
				dragged, selectedROI = selectROI(selectedROI, currentBounds, len(currentSpectrum))
				infobox.setRegion(selectableRegions[selectedROI])

			if dragged:
				zoomButton = Button(screen, paleBlue, screenSize[0] - 120, 5, 100, 2*font_size+10, "Zoom", black)
	
	graphArea.blit(graph, (0, 0))

	if dragging:
		currentMouseX, currentMouseY = pygame.mouse.get_pos()
		currentMouseX -= graphOffset[0]
		dragSurface = pygame.Surface((abs(dragging[0] - currentMouseX), graphSize[1])).convert()
		dragSurface.set_alpha(70)
		dragSurface.fill(paleBlue)
		graphArea.blit(dragSurface, (min((dragging[0], currentMouseX)), 0))
	elif dragged:
		graphArea.blit(dragged[0].convert(), (dragged[1], 0))
		zoomButton.repaint(None)

	if unzoom:
		unzoomButton.repaint(None)
			
	linLogButton.repaint(buttonText)
	infobox.paint()
	screen.blit(infobox.surface.convert(), (130, 0))
	screen.blit(graphArea, graphOffset)
	pygame.display.update()
