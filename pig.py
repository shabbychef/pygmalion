#! /usr/bin/env python
# coding: utf-8
#
"""
.. module pygmalion:: pygmalion
   :synopsis: Pass the Pigs game

.. moduleauthor: Steven E. Pav <steven@gilgamath.com>

    Created: 2024.05.03
    Copyright: Steven E. Pav, 2024
    Author: Steven E. Pav
    Comments: Steven E. Pav
"""

from dice import ListProbabilityDistribution

from enum import Enum, IntEnum, auto

class PigState(IntEnum):
    """
    the states of a pig roll
    """
    DOT_UP = auto()
    DOT_DOWN = auto()
    TROTTER = auto()
    RAZORBACK = auto()
    SNOUTER = auto()
    LEANING_JOWLER = auto()

# from table 4 in Kern, http://jse.amstat.org/v14n3/datasets.kern.html we have
# the following outcomes from 6000 rolls (there were 23 making bacon)

Roll_history = {PigState.DOT_UP: [573,656,139,360,56,12],
        PigState.DOT_DOWN: [623,731,185,449,58,17],
        PigState.TROTTER: [155,180,45,149,17,5],
        PigState.RAZORBACK: [396,473,124,308,45,8],
        PigState.SNOUTER: [54,67,13,47,2,1],
        PigState.LEANING_JOWLER: [10,10,0,7,1,1],
        }

# sum([sum(val) for val in Roll_history.values()])

PigRolls = ListProbabilityDistribution.from_duplicated(list(Roll_history.keys()), [sum(x) for x in Roll_history.values()])
PigRolls.pmf_dict

TwoPigRolls = PigRolls**2

doh = TwoPigRolls.sample(5977)
coco = Counter()
coco.update(doh)

TwoPigRolls = PigRolls | PigRolls


# need a sorted product for ordered distributions...

#for vim modeline: (do not edit)
# vim:ts=4:sw=4:sts=4:tw=79:sta:et:ai:nu:fdm=indent:syn=python:ft=python:tag=.py_tags;:cin:fo=croql
