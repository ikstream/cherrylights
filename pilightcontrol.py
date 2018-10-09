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

from recordtype import recordtype

import pigpio

ON = 1
OFF = 0

PWM_MAX = 255
PWM_MIN = 0

STEP_MIN = 0
STEP_MAX = 255

RED = 0
GREEN = 1
BLUE = 2

DECR = -1
INCR = 1

class LightControl(object):
    """
    Contains information and action about the light control
    """

    f_lights = {'ub' : 0,
                'lb' : 0,
                'ur' : 0,
                'lr' : 0,
                'ul' : 0,
                'll' : 0
               }

    def __init__(self, path):
        self.__lights = dict()
        self.__config = configparser.ConfigParser()
        self.__content = self.__config.read(path)
        self.__pi_ip = self.get_addresses_from_config()
        self.__lower_limit = 5
        self.__upper_limit = 255
        self.__fade_time = 0.1
        self.__step_size = 1
        self.disable_fade()
        #self.turn_pi_lights(OFF)


    def get_config(self):
        """
        return config_content to user
        """
        return self.__config


    def get_addresses_from_config(self):
        """
        Get IP addresses used as sections in config

        :return (list): list of IP addresses from config
        """
        return self.__config.sections()


    def get_light_names(self, ip):
        """
        return the names used for lights in config file
        these names have to be unique

        :param: ip (string): ip address of the pi to handle

        return (list): list of light names
        """
        return [light for light in self.__config[ip]]


    def get_light_pins_from_config(self, ip, light):
        """
        retrieve lights as keys value pairs

        :param: ip (string): IP address of the pi to handle
        :param: light (string): name of light to get pins from

        return (list): list with pins of lights
        """
        return self.__config[ip][light].split(',')

    def get_lower_limit(self):
        """
        get minimum pwm limit

        :return (int): lower limit for pwm
        """
        return self.__lower_limit


    def set_lower_limit(self, limit):
        """
        set minimum pwm limit

        :param limit (int): lower limit for pwm
        """
        self.__lower_limit = limit if limit >= PWM_MIN else PWM_MIN


    def get_upper_limit(self):
        """
        get upper pwm limit

        :return (int): upper limit for pwm
        """
        return self.__upper_limit


    def set_upper_limit(self, limit):
        """
        set upper limit for pwm

        :param limit (int): upper limit for pwm
        """
        self.__upper_limit = limit if limit <= PWM_MAX else PWM_MAX


    def get_fade_time(self):
        """
        get time waited between value changes in seconds

        :return (int): time between two value changes in seconds
        """
        return self.__fade_time


    def set_fade_time(self, fade_time):
        """
        set time waited between value changes in seconds

        :param fade_time (int): time between two value changes in seconds
        """
        self.__fade_time = fade_time


    def get_step_size(self):
        """
        get size of pwm steps (0-255)

        :return (int): size of steps for pwm
        """
        return self.__step_size


    def set_step_size(self, step_size):
        """
        set size of pwm steps (0-255)

        :param step_size (int): size of pwm step (0-255)
        """
        if STEP_MIN <= step_size <= STEP_MAX:
            self.__step_size = step_size
        elif step_size < STEP_MIN:
            self.__step_size = STEP_MIN
        else:
            self.__step_size = STEP_MAX


    def disable_fade(self):
        """
        initialize all lights not to fade
        """
        self.f_lights = {f_light: 0 for f_light in self.f_lights}


    def set_fade(self, light):
        """
        set light to fade

        :param: light (string): light to activate
        """
        self.f_lights[light] = 1


    def unset_fade(self, light):
        """
        set light not to fade

        :param light (string): light to deactivate
        """
        self.f_lights[light] = 0


    def resolve_pi(self, light):
        """
        Get pi to use

        :param: light (string): light to check

        :return (string): IP of pi controlling the light
        """
        for ip in self.__pi_ip:
            if light in self.get_light_names(ip):
                return ip


    def resolve_lights(self, **web_lights):
        """
        set LED strips to work on

        :param web_lights (dict): lights to work on, contains all set lights
        """
        for key in web_lights:
            self.__lights[re.search(r'\[(.*?)\]', key).group(1)] = web_lights[key]


    def get_pin_values(self, light):
        """
        retrieve values of light pins

        :param light (string): light to check pin values on

        :return (list): values of r/g/b pins
        """
        control_pi = self.resolve_pi(light)
        r_pin, g_pin, b_pin = self.get_light_pins_from_config(control_pi, light)

        fade_red = control_pi.get_PWM_dutycycle(r_pin)
        fade_green = control_pi.get_PWM_dutycycle(g_pin)
        fade_blue = control_pi.get_PWM_dutycycle(b_pin)

        return [fade_red, fade_green, fade_blue]



    def __adjust_color(self, color, direction, ip, pin):
        """
        Adjust colors during fade

        :param color (Color/recordtype): color to change
        :param direction (int): increase (1) or reduce (-1)
        :param ip (string): ip of pi to change light
        :param pin (int): pin to change

        :return (Color/recordtype) update color information
        """
        color.color_value += direction * color.alter_color
        value = color.color_value

        if color.color_value < self.__lower_limit:
            #dim color to zero
            value = self.__lower_limit
            color.color_value = self.__lower_limit
            color.alter_color = OFF
            color.change_next = -1

        if color.color_value > (self.__upper_limit - self.__lower_limit):
            #set color to 255
            value = self.__upper_limit
            color.color_value = self.__upper_limit
            color.alter_color = OFF
            color.change_next = 1

        ip.set_PWM_dutycycle(pin, value)
        return color


    # fade light
    def fade_light(self, light):
        """
        per LED strip fade function

        :param light (string): light to fade
        """
        color = recordtype('Color', ['alter_color', 'color_value',
                                     'change_next'])

        ip = self.resolve_pi(light)
        r_pin, g_pin, b_pin = self.get_light_pins_from_config(ip, light)
        pin_values = self.get_pin_values(light)
        red = color(0, pin_values[RED], DECR)
        green = color(self.__step_size, pin_values[GREEN], 0)
        blue = color(0, pin_values[BLUE], 0)


        while self.f_lights[light]:
            if red.change_next:
                green = self.__adjust_color(green, red.change_next, ip, g_pin)
                time.sleep(self.__fade_time)

            if green.change_next:
                blue = self.__adjust_color(blue, green.change_next, ip, b_pin)
                time.sleep(self.__fade_time)

            if blue.change_next:
                red = self.__adjust_color(red, blue.change_next, ip, r_pin)
                time.sleep(self.__fade_time)


    def fade_lights(self, **web_lights):
        """
        start fade for selected LED strips
        """
        self.resolve_lights(**web_lights)
        print("in fadeLights")
        for light in self.__lights:
            self.set_fade(light)
            threading.Thread(target=self.fade_light, args=(light,)).start()
        self.__lights = {}


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
