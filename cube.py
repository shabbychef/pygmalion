#! /usr/bin/env python
# coding: utf-8
#
"""
.. module pygmalion:: pygmalion
   :synopsis: rubiks cube nonsense.

.. moduleauthor: Steven E. Pav <steven@gilgamath.com>

    Created: 2024.05.06
    Copyright: Steven E. Pav, 2024
    Author: Steven E. Pav
    Comments: Steven E. Pav
"""


class TwoCube:
    __remap = {
        "R+": [0, 3, 2, 7, 4, 1, 6, 5],
        "R-": [0, 5, 2, 1, 4, 7, 6, 3],
        "T+": [1, 5, 2, 3, 0, 4, 6, 7],
        "T-": [4, 0, 2, 3, 5, 1, 6, 7],
        "F+": [2, 0, 3, 1, 4, 5, 6, 7],
        "F-": [1, 3, 0, 2, 4, 5, 6, 7],
    }
    """ A two by two cube. """

    def __init__(self, state=None):
        """TwoCube object instantiation."""
        if state is None:
            state = list(range(8))
        self.state = state

    def __repr__(self):
        as_str = f"{self.state[4]} {self.state[5]} \\\n{self.state[6]} {self.state[7]}  \\\n\\  {self.state[0]} {self.state[1]}\n \\ {self.state[2]} {self.state[3]}"
        return as_str

    @classmethod
    @property
    def moves(cls):
        """
        returns all possible moves
        """
        return list(cls.__remap.keys())

    def apply(self, themove):
        new_state = [self.state[self.__remap[themove][idx]] for idx in range(8)]
        self.state = new_state

    def apply_many(self, moves):
        # should first remove any elements that are direct inverses.
        # that is R+, followed by R- should be excised.
        for themove in moves:
            self.apply(themove)


def test_cube():
    foo = TwoCube()
    for move in TwoCube.moves:
        foo.apply(move)


# now randomly search for a pattern
import random

for i in range(10):
    moves = random.choices(TwoCube.moves, k=10)
    ace = TwoCube()
    ace.apply_many(moves)
    if sum([val == i for i, val in enumerate(ace.state)]) == 5:
        print(moves)

# this one keeps 5 in place
moves = ["R+", "T+", "F+", "R-", "T-", "T+", "T-", "F-", "R-", "T+"]
ace = TwoCube()
ace.apply_many(moves)

for i in range(1000):
    moves = random.choices(TwoCube.moves, k=6)
    ace = TwoCube()
    ace.apply_many(moves)
    if sum([val == i for i, val in enumerate(ace.state)]) == 5:
        print(moves)

["T+", "R+", "T-", "R-", "T-", "F-"]
["T-", "T-", "R+", "T-", "R-", "F+"]
["T-", "R+", "F+", "R-", "F-", "R-"]
["F+", "T+", "R+", "T-", "F-", "T+"]
["R-", "T-", "R+", "T+", "R+", "F+"]
["T+", "F+", "R-", "T+", "T+", "F-"]
["F+", "F+", "T-", "R+", "T+", "R-"]
["R+", "F+", "R-", "F-", "R-", "T-"]

allem = [TwoCube.moves] * 4
import itertools

for moves in itertools.product(*allem):
    ace = TwoCube()
    ace.apply_many(moves)
    if sum([val == i for i, val in enumerate(ace.state)]) == 3:
        print(moves)

moves = ["T+", "R+", "T-", "R-", "T-", "F-"]
ace = TwoCube()
ace.apply_many(moves)
ace

# for vim modeline: (do not edit)
# vim:ts=4:sw=4:sts=4:tw=79:sta:et:ai:nu:fdm=indent:syn=python:ft=python:tag=.py_tags;:cin:fo=croql
