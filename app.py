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

import cherrypy
from cherrypy.lib.static import serve_file

GPIO.setmode(GPIO.BCM)

path = os.path.abspath(os.path.dirname(__file__))
CURDIR = os.getcwd()

cherrypy.config.update({
    "tools.staticdir.dir": CURDIR,
    "tools.staticdir.on": True,
    "server.socket_host": "192.168.0.5"
})

#define some values for later use
FULL = 255
OFF = 0

back_pins = {
    'UB_RED' : '18',
    'UB_GREEN' : '23',
    'UB_BLU' : '24',
    'LB_RED' : '25',
    'LB_GREEN' : '8',
    'LB_BLUE' : '7'
}

front_pins = {
    'UR_RED': '18',
    'UR_GREEN': '23',
    'UR_BLUE': '24',
    'LR_RED': '25',
    'LR_GREEN': '8',
    'LR_BLUE': '7',
    'UL_RED': '17',
    'UL_GREEN': '21',
    'UL_BLUE': '22',
    'LL_RED': '10',
    'LL_GREEN': '9',
    'LL_BLUE': '11'
}

lights = {}

remote_pi = '192.168.0.10'
pi = pigpio.pi()
front_pi = pigpio.pi(remote_pi)


class LightControll(object):

    lights = {}

    def __init__(self):
        for pin in back_pins.values():
            pi.set_PWM_dutycycle(pin, OFF)

        for pin in front_pins.values():
            front_pi.set_PWM_dutycycle(pin, OFF)


    @cherrypy.expose
    def index(self):
        return serve_file(os.path.join(path, 'index.html'))


    def setRealValue(value):
        return int(int(value) * (float(bright) / 255.0))


    @cherrypy.expose
    def setLights(self, **web_lights):
        lights = web_lights
        for light in lights:
            print("light: {}: {}\n".format(light, lights[light]))


    def fade_lights(self):
        x = 5


    @cherrypy.expose
    def pickColor(self, **colors):
        red = colors['red']
        green = colors['green']
        blue = colors['blue']

        for light in lights.keys():
            [pin for key, pin in back_pins.items() if str(light).upper() in key]
            [color for color, value in back_pins.items() if str(key).lower in color]
            pi.set_PWM_dutycycle(pin, value)
        #TODO: create sublistst for each light with partial key matching
        #   Then set values accordingly
        if red:
            GPIO.output(self.RED_LED, True)
            print("red: {} ".format(red))
        if green:
            GPIO.output(self.GREEN_LED, True)
            print("green: {} ".format(green))
        if blue:
            GPIO.output(self.BLUE_LED, True)
            print("blue {}\n".format(blue))

        for color in colors:
            print("{}: {}".format(color, colors[color]))


    @cherrypy.expose
    def controlButtonClick(self, id):
        print("id: {}\n".format(id))
        if id in 'off':
            for pin in back_pins.values():
                pi.set_PWM_dutycycle(pin, OFF)

            for pin in front_pins.values():
                front_pi.set_PWM_dutycycle(pin, OFF)

        if id in 'on':
            for pin in back_pins.values():
                pi.set_PWM_dutycycle(pin, OFF)

            for pin in front_pins.values():
                front_pi.set_PWM_dutycycle(pin, OFF)

    def hex_to_val(hexstring):
        #TODO: calculate rgb values vrom hex string
        x=42
        rgb = []
        return rgb


    @cherrypy.expose
    @cherrypy.tools.json_out()
    def colorButtonClick(self, id, val):
        rgb = hex_to_val(val)
        if id:
            if id in 'green':
                GPIO.output(self.GREEN_LED, True)
                GPIO.output(self.BLUE_LED, False)
                GPIO.output(self.RED_LED, False)
            elif id in 'blue':
                GPIO.output(self.GREEN_LED, False)
                GPIO.output(self.BLUE_LED, True)
                GPIO.output(self.RED_LED, False)

            elif id in 'red':
                GPIO.output(self.GREEN_LED, False)
                GPIO.output(self.BLUE_LED, False)
                GPIO.output(self.RED_LED, True)
            elif id in 'white':
                GPIO.output(self.GREEN_LED, True)
                GPIO.output(self.RED_LED, True)
                GPIO.output(self.BLUE_LED, True)
            elif id in 'purple':
                GPIO.output(self.GREEN_LED, False)
                GPIO.output(self.RED_LED, True)
                GPIO.output(self.BLUE_LED, True)
            elif id in 'orange':
                GPIO.output(self.GREEN_LED, True)
                GPIO.output(self.RED_LED, True)
                GPIO.output(self.BLUE_LED, False)
            elif id in 'yellow':
                GPIO.output(self.GREEN_LED, True)
                GPIO.output(self.RED_LED, True)
                GPIO.output(self.BLUE_LED, False)

        return json.dumps({"button": "{}" .format(id)})


if __name__ == '__main__':
    cherrypy.quickstart(LightControll(), '/')
