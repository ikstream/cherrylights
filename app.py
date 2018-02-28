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

import pigpio
import cherrypy
from cherrypy.lib.static import serve_file

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

BACK_PI_LIGHTS = {
    'ub' : [13, 19, 26],
    'lb' : [16, 20, 21]
}

FRONT_PI_LIGHTS = {
    'ur' : [18, 23, 24],
    'lr' : [16, 20, 21],
    'ul' : [17, 27, 22],
    'll' : [13, 19, 26]
}


FRONT_PI_IP = '192.168.0.6'
BACK_PI = pigpio.pi()
FRONT_PI = pigpio.pi(FRONT_PI_IP)

class LightControll(object):
    """Contains information and action about the light control"""
    lights = {}

    f_lights = {'ub' : 0,
                'lb' : 0,
                'ur' : 0,
                'lr' : 0,
                'ul' : 0,
                'll' : 0
               }

    # fade functions
    @classmethod
    def init_fade(cls):
        """initialize all lights not to fade"""
        cls.f_lights = {f_light: 0 for f_light in cls.f_lights}


    @classmethod
    def set_fade(cls, light):
        """set light to fade"""
        cls.f_lights[light] = 1


    @classmethod
    def unset_fade(cls, light):
        """set light not to fade"""
        cls.f_lights[light] = 0


    @staticmethod
    def resolve_pi(light):
        """return pi to use"""
        if light in BACK_PI_LIGHTS:
            return BACK_PI

        return FRONT_PI


    @staticmethod
    def resolve_pi_lights(light):
        """return light array to use"""
        if light in BACK_PI_LIGHTS:
            return BACK_PI_LIGHTS

        return FRONT_PI_LIGHTS

    @classmethod
    def resolve_pins(cls, light):
        """return the pin numbers for a given light"""
        c_light = cls.resolve_pi_lights(light)
        return c_light[light]

    # set lights to use
    def resolve_lights(self, **web_lights):
        """set LED strips to work on"""
        for key in web_lights:
            self.lights[re.search(r'\[(.*?)\]', key).group(1)] = web_lights[key]
        print("weblights {}".format(web_lights))
        print("lights: {}".format(self.lights))


    # show website
    @cherrypy.expose
    def index(self):
        """serve HTML file"""
        return serve_file(os.path.join(PATH, 'index.html'))


    # set color on color button click
    @cherrypy.expose
    def set_lights(self, red, green, blue, **web_lights):
        """set static color for LED Strips"""
        self.resolve_lights(**web_lights)
        for light in self.lights:
            self.unset_fade(light)
            control_pi = self.resolve_pi(light)
            c_light = self.resolve_pi_lights(light)
            print("light: {}: {}\n".format(light, self.lights[light]))
            control_pi.set_PWM_dutycycle(int(c_light[light][R]), red)
            control_pi.set_PWM_dutycycle(int(c_light[light][G]), green)
            control_pi.set_PWM_dutycycle(int(c_light[light][B]), blue)

        self.lights = {}


    # fade light
    @classmethod
    def fade_light(cls, light):
        """per LED strip fade function"""
        dim_green = 1
        dim_blue = 0

        control_pi = cls.resolve_pi(light)
        r_pin, g_pin, b_pin = cls.resolve_pins(light)

        fade_red = control_pi.get_PWM_dutycycle(r_pin)
        fade_green = control_pi.get_PWM_dutycycle(g_pin)
        fade_blue = control_pi.get_PWM_dutycycle(b_pin)

        while cls.f_lights[light]:
            # dim green to zero
            if fade_green > 4 and dim_green:
                control_pi.set_PWM_dutycycle(g_pin, fade_green - 5)

                fade_green -= 5
                time.sleep(0.5)
                continue
            elif fade_green <= 4 and dim_green:
                control_pi.set_PWM_dutycycle(g_pin, OFF)

                fade_green = 0
                dim_green = 0
                dim_blue = 1
                time.sleep(0.5)

            # dim blue to zero
            if fade_blue > 4 and dim_blue:
                control_pi.set_PWM_dutycycle(b_pin, fade_green - 5)

                fade_blue -= 5
                time.sleep(0.5)
                continue
            elif fade_blue <= 4 and dim_blue:
                control_pi.set_PWM_dutycycle(b_pin, OFF)

                fade_blue = 0
                dim_blue = 0

            # increase red to 255
            if fade_red < 251:
                control_pi.set_PWM_dutycycle(r_pin, fade_red + 5)

                fade_red += 5
                time.sleep(0.5)
                continue
            elif fade_red >= 251 and fade_red < 255:
                control_pi.set_PWM_dutycycle(r_pin, ON)

                fade_red = ON
                time.sleep(0.5)

            # increase green to 255
            if fade_green < 251:
                control_pi.set_PWM_dutycycle(g_pin, fade_green + 5)

                fade_green += 5
                time.sleep(0.5)
                continue
            elif fade_green >= 251 and fade_green < 255:
                control_pi.set_PWM_dutycycle(g_pin, ON)

                fade_green = ON
                time.sleep(0.5)

            # increase blue to 255
            if fade_blue < 251:
                control_pi.set_PWM_dutycycle(b_pin, fade_blue + 5)

                fade_blue += 5
                time.sleep(0.5)
                continue
            elif fade_blue >= 251 and fade_blue < 255:
                control_pi.set_PWM_dutycycle(b_pin, ON)

                fade_blue = ON
                time.sleep(0.5)
                dim_red = 1

            # dim red to zero
            if fade_red > 4 and dim_red:
                control_pi.set_PWM_dutycycle(r_pin, fade_red - 5)

                fade_red -= 5
                time.sleep(0.5)
                continue
            elif fade_red <= 4 and dim_red:
                control_pi.set_PWM_dutycycle(r_pin, OFF)

                fade_red = 0
                time.sleep(0.5)


    def fade_lights(self, **web_lights):
        """start fade for selected LED strips"""
        self.resolve_lights(**web_lights)
        print("in fadeLights")
        for light in self.lights:
            self.set_fade(light)
            light_array = self.resolve_pi_lights(light)
            fade_args = [light_array[light][R], light_array[light][G],
                         light_array[light][B], light]
            threading.Thread(target=self.fade_light, args=(fade_args,)).start()
        self.lights = {}


    @staticmethod
    def turn_pi_lights(state):
        """switch all lights on/off"""
        for light in BACK_PI_LIGHTS.values():
            print(light)
            if BACK_PI.connected:
                for pin in light:
                    print(pin)
                    BACK_PI.set_PWM_dutycycle(int(pin), state)
        for light in FRONT_PI_LIGHTS.values():
            print(light)
            if FRONT_PI.connected:
                for pin in light:
                    print(pin)
                    FRONT_PI.set_PWM_dutycycle(int(pin), state)


    @cherrypy.expose
    def control_button_click(self, button_id, **web_lights):
        """backend for buttons on webinterface - react on button click"""
        print("button_id: {}\n".format(button_id))
        if button_id in 'off':
            print("in off")
            self.turn_pi_lights(OFF)

        if button_id in 'on':
            self.init_fade()
            print("in on")
            self.turn_pi_lights(ON)

        if button_id in 'fade':
            print("in fade")
            if web_lights:
                self.fade_lights(**web_lights)


    def __init__(self):
        self.init_fade()
        self.turn_pi_lights(OFF)



if __name__ == '__main__':
    cherrypy.quickstart(LightControll(), '/')
