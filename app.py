#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

import RPi.GPIO as GPIO
import pigpio

import os
import json
import re

import cherrypy
from cherrypy.lib.static import serve_file


path = os.path.abspath(os.path.dirname(__file__))
CURDIR = os.getcwd()

cherrypy.config.update({
    "tools.staticdir.dir": CURDIR,
    "tools.staticdir.on": True,
    "server.socket_host": "192.168.0.10"
})

#define some values for later use
ON = 255
OFF = 0

back_pi_lights = {
        'ub' : [13, 19, 26],
        'lb' : [16, 20, 21]
}

front_pi_lights = {
        'ur' : [18, 23, 24],
        'lr' : [16, 20, 21],
        'ul' : [17, 27, 22],
        'll' : [13, 19, 26]
}


#front_pi_ip = '192.168.0.6'
back_pi = pigpio.pi()
#front_pi = pigpio.pi(front_pi_ip)


class LightControll(object):

    lights = {}

    def __init__(self):
        for light in back_pi_lights.values():
            print(light)
            for pin in light:
                print(pin)
                back_pi.set_PWM_dutycycle(int(pin), OFF)


    def resolveLights(self, **web_lights):
        for key in web_lights:
            self.lights[re.search(r'\[(.*?)\]',key).group(1)] = web_lights[key]
        print("weblights {}".format(web_lights))
        print("lights: {}".format(self.lights))


    @cherrypy.expose
    def index(self):
        return serve_file(os.path.join(path, 'index.html'))


    def setRealValue(value):
        return int(int(value) * (float(bright) / 255.0))


    @cherrypy.expose
    def setLights(self, red, green, blue, **web_lights):
        self.resolveLights(**web_lights)
        for light in self.lights:
            print("light: {}: {}\n".format(light, self.lights[light]))
            if light in back_pi_lights:
                    back_pi.set_PWM_dutycycle(int(back_pi_lights[light][0]), red)
                    back_pi.set_PWM_dutycycle(int(back_pi_lights[light][1]), green)
                    back_pi.set_PWM_dutycycle(int(back_pi_lights[light][2]), blue)
        self.lights = {}


    def fadeLights(self, **web_lights):
        self.resolveLights(**web_lights)
        print("in fadeLights")
        x = 5
        self.lights = {}


    @cherrypy.expose
    def controlButtonClick(self, id, **web_lights):
        print("id: {}\n".format(id))
        if id in 'off':
            print("in off")
            for light in back_pi_lights.values():
                for pin in light:
                    print(pin)
                    back_pi.set_PWM_dutycycle(int(pin), OFF)

        if id in 'on':
            print("in on")
            for light in back_pi_lights.values():
                for pin in light:
                    print(pin)
                    back_pi.set_PWM_dutycycle(int(pin), ON)

        if id in 'fade':
            print("in fade")
            if web_lights:
                self.fadeLights(**web_lights)


if __name__ == '__main__':
    cherrypy.quickstart(LightControll(), '/')
