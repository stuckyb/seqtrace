# Copyright (C) 2018 Brian J. Stucky
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# This module defines several functions for working with Gdk.RGBA colors.


import gi
from gi.repository import Gdk


def parseHTMLColorStr(html_color):
    """
    Returns a Gdk.RGBA instance that represents the given HTML color string.
    """
    color = Gdk.RGBA()
    color.parse(html_color)

    return color

def getInverseColor(color):
    """
    Returns a Gdk.RGBA that is the inverse of the provided color.
    """
    invcolor = Gdk.RGBA()
    invcolor.red = 1.0 - color.red
    invcolor.green = 1.0 - color.green
    invcolor.blue = 1.0 - color.blue

    return invcolor

def colorFromHSV(hue, saturation, value):
    """
    Returns a Gdk.RGBA instance that represents the given HSV values.  For
    consistency with the original GDK color_from_hsv function, all inputs
    should be floats in the range 0.0 - 1.0.
    """
    chroma = saturation * value
    hprime = hue * 6.0
    x = chroma * (1 - abs(hprime % 2 - 1))

    rgb = (0, 0, 0)
    if hprime <= 1:
        rgb = (chroma, x, 0)
    elif hprime <= 2:
        rgb = (x, chroma, 0)
    elif hprime <= 3:
        rgb = (0, chroma, x)
    elif hprime <= 4:
        rgb = (0, x, chroma)
    elif hprime <= 5:
        rgb = (x, 0, chroma)
    elif hprime <= 6:
        rgb = (chroma, 0, x)

    m = value - chroma
    color = Gdk.RGBA(rgb[0] + m, rgb[1] + m, rgb[2] + m)

    return color

