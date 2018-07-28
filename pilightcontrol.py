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

import configparser
import os
import re
import time
import threading
import socket

import pigpio

class LightControl(object):
    """
    Contains information and action about the light control
    """
    lights = {}

    f_lights = {'ub' : 0,
                'lb' : 0,
                'ur' : 0,
                'lr' : 0,
                'ul' : 0,
                'll' : 0
               }

    def __init__(self, path):
        self.__config = configparser.ConfigParser()
        self.__content = self.__config.read(path)
        self.init_fade()
        #self.turn_pi_lights(OFF)


    def get_config(self):
        """
        return config_content to user
        """
        return self.__config


    def get_addresses_from_config(self):
        """
        return ip addresses used as sections in config

        @type config configparser.ConfigParser
        @param config configuration to read from
        """
        return self.__config.sections()


    def get_light_names(self, ip):
        """
        return the names used for lights in config file
        these names have to be unique
        """
        return [light for light in self.__config[ip]]


    def get_light_pins_from_config(self, ip, light):
        """
        retrieve lights as keys value pairs
        returns a dictionary
        """
        return self.__config[ip][light].split(',')


    # fade functions
    def init_fade(self):
        """
        initialize all lights not to fade
        """
        self.f_lights = {f_light: 0 for f_light in self.f_lights}


    @classmethod
    def set_fade(self, light):
        """
        set light to fade
        """
        self.f_lights[light] = 1


    @classmethod
    def unset_fade(self, light):
        """
        set light not to fade
        """
        self.f_lights[light] = 0


    @staticmethod
    def resolve_pi(light):
        """
        return pi to use
        """
        if light in BACK_PI_LIGHTS:
            return BACK_PI

        return FRONT_PI


    @staticmethod
    def resolve_pi_lights(light):
        """
        return light array to use
        """
        if light in BACK_PI_LIGHTS:
            return BACK_PI_LIGHTS

        return FRONT_PI_LIGHTS

    @classmethod
    def resolve_pins(self, light):
        """
        return the pin numbers for a given light
        """
        c_light = self.resolve_pi_lights(light)
        return c_light[light]

    # set lights to use
    def resolve_lights(self, **web_lights):
        """
        set LED strips to work on
        """
        for key in web_lights:
            self.lights[re.search(r'\[(.*?)\]', key).group(1)] = web_lights[key]
        print("weblights {}".format(web_lights))
        print("lights: {}".format(self.lights))


    # fade light
    @classmethod
    def fade_light(self, light):
        """
        per LED strip fade function
        """
        alter_green = -STEP_SIZE
        alter_blue = 0
        alter_red = 0

        control_pi = self.resolve_pi(light)
        r_pin, g_pin, b_pin = self.resolve_pins(light)

        fade_red = control_pi.get_PWM_dutycycle(r_pin)
        fade_green = control_pi.get_PWM_dutycycle(g_pin)
        fade_blue = control_pi.get_PWM_dutycycle(b_pin)

        while self.f_lights[light]:
            if alter_green:
                fade_green += alter_green
                if fade_green < LOWER_LIMIT:
                    # dim green to 0
                    control_pi.set_PWM_dutycycle(g_pin, LOWER_LIMIT)
                    fade_green = LOWER_LIMIT
                    alter_green = OFF
                    alter_blue = -STEP_SIZE
                    time.sleep(FADE_TIME)
                    continue

                if fade_green > (ON - STEP_SIZE):
                    # set green to 255
                    control_pi.set_PWM_dutycycle(g_pin, ON)
                    fade_green = ON
                    alter_green = OFF
                    alter_blue = STEP_SIZE
                    time.sleep(FADE_TIME)
                    continue

                # change green by STEP_SIZE
                control_pi.set_PWM_dutycycle(g_pin, fade_green)
                time.sleep(FADE_TIME)

            if alter_blue:
                fade_blue += alter_blue
                if fade_blue < LOWER_LIMIT:
                    # dim blue to 0
                    control_pi.set_PWM_dutycycle(b_pin, LOWER_LIMIT)
                    fade_blue = LOWER_LIMIT
                    alter_blue = OFF
                    alter_red = STEP_SIZE
                    time.sleep(FADE_TIME)
                    continue

                if fade_blue > (ON - STEP_SIZE):
                    # set blue to 255
                    control_pi.set_PWM_dutycycle(b_pin, ON)
                    fade_blue = ON
                    alter_blue = OFF
                    alter_red = -STEP_SIZE
                    time.sleep(FADE_TIME)
                    continue

                # change green by STEP_SIZE
                control_pi.set_PWM_dutycycle(b_pin, fade_blue)
                time.sleep(FADE_TIME)

            if alter_red:
                fade_red += alter_red
                if fade_red < LOWER_LIMIT:
                    # dim red to 0
                    control_pi.set_PWM_dutycycle(r_pin, fade_red)
                    fade_red = LOWER_LIMIT
                    alter_red = OFF
                    alter_green = -STEP_SIZE
                    time.sleep(FADE_TIME)
                    continue

                if fade_red > (ON - STEP_SIZE):
                    # set red to 255
                    control_pi.set_PWM_dutycycle(r_pin, ON)
                    fade_red = ON
                    alter_red = OFF
                    alter_green = STEP_SIZE
                    time.sleep(FADE_TIME)
                    continue

                # change red by STEP_SIZE
                control_pi.set_PWM_dutycycle(r_pin, fade_red)
                time.sleep(FADE_TIME)



    def fade_lights(self, **web_lights):
        """
        start fade for selected LED strips
        """
        self.resolve_lights(**web_lights)
        print("in fadeLights")
        for light in self.lights:
            self.set_fade(light)
            threading.Thread(target=self.fade_light, args=(light,)).start()
        self.lights = {}


    @staticmethod
    def turn_pi_lights(state):
        """
        switch all lights on/off
        """
        for light in BACK_PI_LIGHTS:
            LightControll.unset_fade(light)
            print(light)
            if BACK_PI.connected:
                for pin in BACK_PI_LIGHTS[light]:
                    print(pin)
                    BACK_PI.set_PWM_dutycycle(int(pin), state)
        for light in FRONT_PI_LIGHTS:
            print(light)
            if FRONT_PI.connected:
                for pin in FRONT_PI_LIGHTS[light]:
                    print(pin)
                    FRONT_PI.set_PWM_dutycycle(int(pin), state)
