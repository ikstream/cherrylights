#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""provide a webfrontend to set 12V LED light strips"""

################################################################################
# MIT License
#
# Copyright (c) 2017 Stefan Venz
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
################################################################################


import os
import re
import time
import threading
import socket

import cherrypy
from cherrypy.lib.static import serve_file

import pilightcontrol as pLC

PATH = os.path.abspath(os.path.dirname(__file__))
CURDIR = os.getcwd()

cherrypy.config.update({
    "tools.staticdir.dir": CURDIR,
    "tools.staticdir.on": True,
    "server.socket_host": socket.gethostbyname(socket.gethostname())
})

#define some values for later use
ON = 255
OFF = 0
R = 0
G = 1
B = 2

#BACK_PI_LIGHTS = { 192.168.2.203
#    'ub' : [13, 19, 26],
#    'lb' : [16, 20, 21]
#}
#
#FRONT_PI_LIGHTS = { 192.168.2.221
#    'ur' : [18, 23, 24],
#    'lr' : [16, 20, 21],
#    'ul' : [17, 27, 22],
#    'll' : [13, 19, 26]
#}


FADE_TIME = 0.1
STEP_SIZE = 1
LOWER_LIMIT = 5

class Root:
    pLC = pLC.LightControl("light.config")

    @cherrypy.expose
    def control_button_click(self, button_id, **web_lights):
        """backend for buttons on webinterface - react on button click"""
        print("button_id: {}\n".format(button_id))
        if button_id in 'off':
            print("in off")
            self.pLC.change_lights_state(OFF)

        if button_id in 'on':
            self.pLC.disable_fade()
            print("in on")
            self.pLC.change_lights_state(ON)

        if button_id in 'fade':
            print("in fade")
            if web_lights:
                self.pLC.fade_lights(**web_lights)


    # show website
    @staticmethod
    @cherrypy.expose
    def index():
        """serve HTML file"""
        return serve_file(os.path.join(PATH, 'index.html'))


    # set color on color button click
    @cherrypy.expose
    def set_lights(self, red, green, blue, **web_lights):
        """set static color for LED Strips"""
        self.pLC.resolve_lights(**web_lights)
        for light in self.pLC.lights:
            self.pLC.unset_fade(light)
            control_pi = self.pLC.resolve_pi(light)
            c_light = self.pLC.resolve_pi_lights(light)
            print("light: {}: {}\n".format(light, self.pLC.lights[light]))
            control_pi.set_PWM_dutycycle(int(c_light[light][R]), red)
            control_pi.set_PWM_dutycycle(int(c_light[light][G]), green)
            control_pi.set_PWM_dutycycle(int(c_light[light][B]), blue)



if __name__ == '__main__':
    cherrypy.quickstart(Root(), '/')
