# -*- coding: utf-8 -*-
"""
chemdataextractor.units.temperatures.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Units and models for times.

Taketomo Isazawa (ti250@cam.ac.uk)

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from .quantities import QuantityModel, Unit, Dimension
from ..parse.elements import W, I, R, Optional, Any, OneOrMore, Not, ZeroOrMore
from ..parse.actions import merge, join

log = logging.getLogger(__name__)


class Time(Dimension):
    pass


class TimeModel(QuantityModel):
    dimensions = Time()


class TimeUnit(Unit):

    def __init__(self, exponent=0.0, powers=None):
        super(TimeUnit, self).__init__(Time(), exponent, powers)


class Second(TimeUnit):

    def convert_to_standard(self, value):
        return value

    def convert_from_standard(self, value):
        return value


class Hour(TimeUnit):

    def convert_to_standard(self, value):
        return value * 60 * 60

    def convert_from_standard(self, value):
        return value / (60**2)


class Minute(TimeUnit):

    def convert_to_standard(self, value):
        return value * 60

    def convert_from_standard(self, value):
        return value / 60


class Year(TimeUnit):

    def convert_to_standard(self, value):
        return value * 60 * 60 * 24 * 365

    def convert_from_standard(self, value):
        return value / (60 * 60 * 24 * 365)


class Day(TimeUnit):

    def convert_to_standard(self, value):
        return value * 60 * 60 * 24

    def convert_from_standard(self, value):
        return value / (60 * 60 * 24)


units_dict = {R('d(ay(s)?)?', group=0): Day, R('y(ear(s)?)?', group=0): Year,
              R('h(our(s)?)?', group=0): Hour, R('s(econd(s)?)?', group=0): Second}
Time.units_dict = units_dict

