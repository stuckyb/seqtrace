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


import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GdkPixbuf
from gi.repository import Pango
import os
import sys


# Set the location of the GUI image files depending on whether we're
# running as a normal Python program or a "frozen" binary.
if hasattr(sys, 'frozen'):
    images_folder = os.path.join(os.path.dirname(sys.executable), 'images')
else:
    images_folder = os.path.dirname(__file__) + '/images'

# Set up the icons for use by all application windows.
Gtk.Window.set_default_icon_list((
    GdkPixbuf.Pixbuf.new_from_file(images_folder + '/icons/16.png'),
    GdkPixbuf.Pixbuf.new_from_file(images_folder + '/icons/32.png'),
    GdkPixbuf.Pixbuf.new_from_file(images_folder + '/icons/48.png'),
    GdkPixbuf.Pixbuf.new_from_file(images_folder + '/icons/64.png')
))


def getDefaultFont():
    """
    Returns the default font used by Gtk+ as a Pango.FontDescription.
    """
    fontstr = Gtk.Settings.get_default().props.gtk_font_name
    default_font = Pango.FontDescription.from_string(fontstr)

    return default_font

