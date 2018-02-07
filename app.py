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


import os
import json
import re
import time
import threading

import cherrypy
from cherrypy.lib.static import serve_file

import pigpio

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
R = 0
G = 1
B = 2

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

fade_lights = { 'ub' : 0,
                'lb' : 0,
                'ur' : 0,
                'lr' : 0,
                'ul' : 0,
                'll' : 0
}

front_pi_ip = '192.168.0.6'
back_pi = pigpio.pi()
front_pi = pigpio.pi(front_pi_ip)

class LightControll(object):
    lights = {}

    def __init__(self):
        self.initFade()
        for light in back_pi_lights.values():
            print(light)
            for pin in light:
                print(pin)
                back_pi.set_PWM_dutycycle(int(pin), OFF)
        for light in front_pi_lights.values():
            print(light)
            for pin in light:
                print(pin)
                front_pi.set_PWM_dutycycle(int(pin), OFF)


    # fade functions
    def initFade(self):
        fade_lights = {fade_light: 0 for fade_light in fade_lights};


    def setFade(self, light):
        if fade_lights[light] == 1:
            fade_lights[light] = 0
            time.sleep(0.2)

        fade_lights[light] = 1


    def unsetFade(self, light):
        fade_lights[light] = 0


    # set lights to use
    def resolveLights(self, **web_lights):
        for key in web_lights:
            self.lights[re.search(r'\[(.*?)\]',key).group(1)] = web_lights[key]
        print("weblights {}".format(web_lights))
        print("lights: {}".format(self.lights))


    # show website
    @cherrypy.expose
    def index(self):
        return serve_file(os.path.join(path, 'index.html'))


    # set color on color button click
    @cherrypy.expose
    def setLights(self, red, green, blue, **web_lights):
        self.resolveLights(**web_lights)
        for light in self.lights:
            self.unsetFade(light)
            print("light: {}: {}\n".format(light, self.lights[light]))
            if light in back_pi_lights:
                back_pi.set_PWM_dutycycle(int(back_pi_lights[light][R]), red)
                back_pi.set_PWM_dutycycle(int(back_pi_lights[light][G]), green)
                back_pi.set_PWM_dutycycle(int(back_pi_lights[light][B]), blue)
            if light in front_pi_lights:
                front_pi.set_PWM_dutycycle(int(front_pi_lights[light][R]), red)
                front_pi.set_PWM_dutycycle(int(front_pi_lights[light][G]), green)
                front_pi.set_PWM_dutycycle(int(front_pi_lights[light][B]), blue)
        self.lights = {}


    # fade light
    def fadeLight(self, r_pin, g_pin, b_pin, light):
        dim_green = 1
        dim_blue = 0
        if light in back_pi_lights:
            fade_red = back_pi.get_PWM_dutycycle(r_pin)
            fade_green = back_pi.get_PWM_dutycycle(g_pin)
            fade_blue = back_pi.get_PWM_dutycycle(b_pin)
        else:
            fade_red = front_pi.get_PWM_dutycycle(r_pin)
            fade_green = front_pi.get_PWM_dutycycle(g_pin)
            fade_blue = front_pi.get_PWM_dutycycle(b_pin)
        while fade_lights[light]:
            # dim green to zero
            if fade_green > 4 and dim_green:
                if light in back_pi_lights:
                    back_pi.set_PWM_dutycycle(g_pin, fade_green - 5)
                else:
                    front_pi.set_PWM_dutycycle(g_pin, fade_green - 5)
                fade_green -= 5
                time.sleep(0.5)
                continue
            elif fade_green <= 4 and dim_green:
                if light in back_pi_lights:
                    back_pi.set_PWM_dutycycle(g_pin, OFF)
                else:
                    front_pi.set_PWM_dutycycle(g_pin, OFF)

                fade_green = 0
                dim_green = 0
                dim_blue = 1
                time.sleep(0.5)

            # dim blue to zero
            if fade_blue > 4 and dim_blue:
                if light in back_pi_lights:
                    back_pi.set_PWM_dutycycle(b_pin, fade_green - 5)
                else:
                    front_pi.set_PWM_dutycycle(b_pin, fade_green - 5)

                fade_blue -= 5
                time.sleep(0.5)
                continue
            elif fade_blue <= 4 and dim_blue:
                if light in back_pi_lights:
                    back_pi.set_PWM_dutycycle(b_pin, OFF)
                else:
                    front_pi.set_PWM_dutycycle(b_pin, OFF)

                fade_blue = 0
                dim_blue = 0

            # increase red to 255
            if fade_red < 251:
                if light in back_pi_lights:
                    back_pi.set_PWM_dutycycle(r_pin, fade_red + 5)
                elif light in front_pi_lights:
                    front_pi.set_PWM_dutycycle(r_pin, fade_red + 5)

                fade_red += 5
                time.sleep(0.5)
                continue
            elif fade_red >= 251 and fade_red < 255:
                if light in back_pi_lights:
                    back_pi.set_PWM_dutycycle(r_pin, ON)
                elif light in front_pi_lights:
                    front_pi.set_PWM_dutycycle(r_pin, ON)

                fade_red = ON
                time.sleep(0.5)

            # increase green to 255
            if fade_green < 251:
                if light in back_pi_lights:
                    back_pi.set_PWM_dutycycle(g_pin, fade_green + 5)
                elif light in front_pi_lights:
                    front_pi.set_PWM_dutycycle(g_pin, fade_green + 5)

                fade_green += 5
                time.sleep(0.5)
                continue
            elif fade_green >= 251 and fade_green < 255:
                if light in back_pi_lights:
                    back_pi.set_PWM_dutycycle(g_pin, ON)
                elif light in front_pi_lights:
                    front_pi.set_PWM_dutycycle(g_pin, ON)

                fade_green = ON
                time.sleep(0.5)

            # increase blue to 255
            if fade_blue < 251:
                if light in back_pi_lights:
                    back_pi.set_PWM_dutycycle(b_pin, fade_blue + 5)
                elif light in front_pi_lights:
                    front_pi.set_PWM_dutycycle(b_pin, fade_blue + 5)

                fade_blue += 5
                time.sleep(0.5)
                continue
            elif fade_blue >= 251 and fade_blue < 255:
                if light in back_pi_lights:
                    back_pi.set_PWM_dutycycle(b_pin, ON)
                elif light in front_pi_lights:
                    front_pi.set_PWM_dutycycle(b_pin, ON)

                fade_blue = ON
                time.sleep(0.5)
                dim_red = 1

            # dim red to zero
            if fade_red > 4 and dim_red:
                if light in back_pi_lights:
                    back_pi.set_PWM_dutycycle(r_pin, fade_red - 5)
                elif light in front_pi_lights:
                    front_pi.set_PWM_dutycycle(r_pin, fade_red - 5)

                fade_red -= 5
                time.sleep(0.5)
                continue
            elif fade_red <= 4 and dim_red:
                if light in back_pi_lights:
                    back_pi.set_PWM_dutycycle(r_pin, OFF)
                elif light in front_pi_lights:
                    front_pi.set_PWM_dutycycle(r_pin, OFF)

                fade_red = 0
                time.sleep(0.5)


    def fadeLights(self, **web_lights):
        self.resolveLights(**web_lights)
        for light in self.lights:
            self.setFade(light)
            if light in back_pi_lights:
                fade_args = [back_pi_lights[light][R], back_pi_lights[light][G], back_pi_lights[light][B], light]
                threading.Thread(target=fadeLight, args=(fade_args,)).start()
            else:
                fade_args = [front_pi_lights[light][R], front_pi_lights[light][G], front_pi_lights[light][B], light]
                threading.Thread(target=fadeLight, args=(fade_args,)).start()

        print("in fadeLights")
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
            for light in front_pi_lights.values():
                for pin in light:
                    print(pin)
                    back_pi.set_PWM_dutycycle(int(pin), OFF)

        if id in 'on':
            self.initFade()
            print("in on")
            for light in back_pi_lights.values():
                for pin in light:
                    print(pin)
                    back_pi.set_PWM_dutycycle(int(pin), ON)
            for light in front_pi_lights.values():
                for pin in light:
                    print(pin)
                    front_pi.set_PWM_dutycycle(int(pin), ON)

        if id in 'fade':
            print("in fade")
            if web_lights:
                self.fadeLights(**web_lights)


if __name__ == '__main__':
    cherrypy.quickstart(LightControll(), '/')
