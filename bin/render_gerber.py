#!/usr/bin/env python
############################################################################################
# Hellen-One: A board rendering script.
# (c) andreika <prometheus.pcb@gmail.com>
############################################################################################

import os, sys

sys.path.append("./bin/pcb-tools")
from gerber import PCB
from gerber.primitives import *
from gerber.render import theme
from gerber.render import RenderSettings
from gerber.render.cairo_backend import GerberCairoContext

if len(sys.argv) < 3:
    print "Error! Please specify the gerber path, image filename and board side."
    sys.exit(1)
gerberPath = sys.argv[1]
imageFileName = sys.argv[2]
boardSide = sys.argv[3]
dpi = sys.argv[4]

# This class is needed only to store the board outline as a filled mask
class HellenGerberCairoContext(GerberCairoContext):
    def __init__(self, scale=600):
        super(HellenGerberCairoContext, self).__init__(scale)
        self.lineList = []

    # this override is needed to adjust the scale to correspond to the given max_width/max_height values
    def render_layers(self, layers, filename, theme, verbose, dpi, isOutline):
        scale = int(dpi)
        self.isOutline = isOutline
        self.scale = (scale, scale)
        self.clear()

        # Render layers
        bgsettings = theme['background']
        for layer in layers:
            settings = theme.get(layer.layer_class, RenderSettings())
            self.render_layer(layer, settings=settings, bgsettings=bgsettings,
                              verbose=verbose)
        self.dump(filename, verbose)
        
    def addPoint(self, start, end, additional):
        start = (start[0] + self.origin_in_pixels[0], start[1] + self.origin_in_pixels[1])
        end = (end[0] + self.origin_in_pixels[0], end[1] + self.origin_in_pixels[1])
        self.lineList.append([start, end, additional])

    # this override is needed to gather all line segments from the outline layers
    def _render_line(self, line, color):
        if self.isOutline == False or self._render_count != 1:		# outline layer
            GerberCairoContext._render_line(self, line, color)
            return
        start = self.scale_point(line.start)
        end = self.scale_point(line.end)
        # we don't draw lines, we store the line segments
        with self._clip_primitive(line):
            self.addPoint(start, end, None)
    
    # this override is needed to gather all arcs from the outline layers
    def _render_arc(self, arc, color):
        if self.isOutline == False or self._render_count != 1:		# outline layer
            GerberCairoContext._render_arc(self, arc, color)
            return
        start = self.scale_point(arc.start)
        end = self.scale_point(arc.end)
        # we don't draw arcs, we store them
        with self._clip_primitive(arc):
    	    self.addPoint(start, end, arc)
    
    # this override is needed to render the actual outline layers in a form of closed filled polygon
    def flatten(self, color=None, alpha=None):
        if self.isOutline == True and self._render_count == 1:		# outline layer
            # reconstruct the contour (the original lines go in no particular order)
            curPoint = self.lineList[0]
            countourPoints = []
            for i in range(1000):
                countourPoints.append([curPoint[0][0], curPoint[0][1], curPoint[2]])
                dist = sys.float_info.max
    		    # find the closest point among the
                for ll in self.lineList:
                    llinv = [ll[1], ll[0], ll[2]]
                    if ll == curPoint or llinv == curPoint:
                        continue
                    d = (ll[0][0] - curPoint[1][0])**2 + (ll[0][1] - curPoint[1][1])**2
                    if d < dist:
                        dist = d
                        nextCurPoint = ll
                    d = (ll[1][0] - curPoint[1][0])**2 + (ll[1][1] - curPoint[1][1])**2
                    if d < dist:
                        dist = d
                        nextCurPoint = llinv
                    if dist < 1.e-4:
                        break
                if nextCurPoint[0] in countourPoints:
                    break
                curPoint = nextCurPoint

            # draw the filled contour    
            with self._new_mask() as mask:
                mask.ctx.move_to(countourPoints[0][0], countourPoints[0][1])
                wasArc = False
                for ll in countourPoints:
                    if ll[2]:
                        arc = ll[2]
                        center = self.scale_point(arc.center)
                        radius = self.scale[0] * arc.radius
                        two_pi = 2 * math.pi
                        angle1 = (arc.start_angle + two_pi) % two_pi
                        angle2 = (arc.end_angle + two_pi) % two_pi
                        if arc.direction == 'counterclockwise':
                            mask.ctx.arc(center[0], center[1], radius, angle1, angle2)
                        else:
                            mask.ctx.arc_negative(center[0], center[1], radius, angle1, angle2)
                    else:
                        mask.ctx.line_to(ll[0], ll[1])
                mask.ctx.set_source_rgba(1.0, 1.0, 1.0, 1.0)
                mask.ctx.fill()
                self.ctx.mask_surface(mask.surface, 0.0, 0.0)
        GerberCairoContext.flatten(self, color, alpha)


###################################################################

# read the gerbers
pcb = PCB.from_directory(gerberPath, None, verbose=True)

outlineTheme = theme.Theme(name='OutlineTheme',
                      background=RenderSettings(theme.COLORS['black'], alpha=0.0),
                      drill=RenderSettings(theme.COLORS['black'], alpha=1.0))
outlineTheme.outline = RenderSettings(theme.COLORS['white'], alpha=1.0)

jlcTheme = theme.Theme(name='JLC',
                      background=RenderSettings(theme.COLORS['fr-4']),
                      top=RenderSettings(theme.COLORS['hasl copper'], alpha=0.85),
                      bottom=RenderSettings(theme.COLORS['hasl copper'], alpha=0.85, mirror=True),
                      topmask=RenderSettings(theme.COLORS['green soldermask'], alpha=0.85, invert=True),
                      bottommask=RenderSettings(theme.COLORS['green soldermask'], alpha=0.85, invert=True, mirror=True),
                      topsilk=RenderSettings(theme.COLORS['white'], alpha=1.0),
                      bottomsilk=RenderSettings(theme.COLORS['white'], alpha=1.0, mirror=True),
                      drill=RenderSettings(theme.COLORS['black'], alpha=1.0))

curTheme = jlcTheme

# choose layers
if boardSide == 'top':
    print "* Top Side:"
    boardLayers = pcb.top_layers + pcb.drill_layers
    isOutline = False
elif boardSide == 'bottom':
    print "* Bottom Side:"
    boardLayers = pcb.bottom_layers + pcb.drill_layers
    isOutline = False
elif boardSide == 'outline':
    print "* Board Outline:"
    boardLayers = [pcb.outline_layer] + pcb.drill_layers
    curTheme = outlineTheme
    isOutline = True
else:
    print "Error! Please specify the valid board side."
    sys.exit(2)

# render
ctx = HellenGerberCairoContext()
ctx.render_layers(layers=boardLayers, filename=imageFileName, theme=curTheme, verbose=True, dpi=dpi, isOutline=isOutline)
