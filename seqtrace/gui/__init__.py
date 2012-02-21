# Copyright (C) 2012 Brian J. Stucky
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


import gtk
import os



# get location of the GUI image files
images_folder = os.path.dirname(__file__) + '/images'

# set up the icons for use by all application windows
gtk.window_set_default_icon_list(
        gtk.gdk.pixbuf_new_from_file(images_folder + '/icons/16.png'),
        gtk.gdk.pixbuf_new_from_file(images_folder + '/icons/32.png'),
        gtk.gdk.pixbuf_new_from_file(images_folder + '/icons/48.png'),
        gtk.gdk.pixbuf_new_from_file(images_folder + '/icons/64.png'))

