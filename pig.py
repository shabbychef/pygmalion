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

import copy
from enum import Enum, IntEnum, auto

from dice import ListProbabilityDistribution, NumericalListProbabilityDistribution


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
# we add the row and column totals.

BACON_PROB = 23 / 6000
Roll_history = {
    PigState.DOT_UP: [573, 656, 139, 360, 56, 12] + [573, 623, 155, 396, 54, 10],
    PigState.DOT_DOWN: [623, 731, 185, 449, 58, 17] + [656, 731, 180, 473, 67, 10],
    PigState.TROTTER: [155, 180, 45, 149, 17, 5] + [139, 185, 45, 124, 13, 0],
    PigState.RAZORBACK: [396, 473, 124, 308, 45, 8] + [360, 449, 149, 308, 47, 7],
    PigState.SNOUTER: [54, 67, 13, 47, 2, 1] + [56, 58, 17, 45, 2, 1],
    PigState.LEANING_JOWLER: [10, 10, 0, 7, 1, 1] + [12, 17, 5, 8, 1, 1],
}

# sum([sum(val) for val in Roll_history.values()])

PigRolls = ListProbabilityDistribution.from_duplicated(
    list(Roll_history.keys()), [sum(x) for x in Roll_history.values()]
)

# this is from Table 3.
PayoffTable = {
    (PigState.DOT_UP, PigState.DOT_UP): 1,
    (PigState.DOT_UP, PigState.DOT_DOWN): 0,
    (PigState.DOT_UP, PigState.TROTTER): 5,
    (PigState.DOT_UP, PigState.RAZORBACK): 5,
    (PigState.DOT_UP, PigState.SNOUTER): 10,
    (PigState.DOT_UP, PigState.LEANING_JOWLER): 15,
    (PigState.DOT_DOWN, PigState.DOT_DOWN): 1,
    (PigState.DOT_DOWN, PigState.TROTTER): 5,
    (PigState.DOT_DOWN, PigState.RAZORBACK): 5,
    (PigState.DOT_DOWN, PigState.SNOUTER): 10,
    (PigState.DOT_DOWN, PigState.LEANING_JOWLER): 15,
    (PigState.TROTTER, PigState.TROTTER): 20,
    (PigState.TROTTER, PigState.RAZORBACK): 10,
    (PigState.TROTTER, PigState.SNOUTER): 15,
    (PigState.TROTTER, PigState.LEANING_JOWLER): 20,
    (PigState.RAZORBACK, PigState.RAZORBACK): 20,
    (PigState.RAZORBACK, PigState.SNOUTER): 15,
    (PigState.RAZORBACK, PigState.LEANING_JOWLER): 20,
    (PigState.SNOUTER, PigState.SNOUTER): 40,
    (PigState.SNOUTER, PigState.LEANING_JOWLER): 25,
    (PigState.LEANING_JOWLER, PigState.LEANING_JOWLER): 60,
}

TwoPigRolls = PigRolls | copy.deepcopy(PigRolls)
PigPayoff = TwoPigRolls.map(lambda x: PayoffTable.get(x, 0))
PigPayoff = NumericalListProbabilityDistribution.from_dict(PigPayoff.pmf_dict)

# need a sorted product for ordered distributions...
def test_pigroll():
    # TwoPigRolls = PigRolls % copy.deepcopy(PigRolls)
    TwoPigRolls = PigRolls | copy.deepcopy(PigRolls)
    TwoPigRolls.generate()
    TwoPigRolls.pmf_dict

def test_pig_payoff():
    ep = PigPayoff.expected_value()
    vp = PigPayoff.variance()


# for vim modeline: (do not edit)
# vim:ts=4:sw=4:sts=4:tw=79:sta:et:ai:nu:fdm=indent:syn=python:ft=python:tag=.py_tags;:cin:fo=croql
