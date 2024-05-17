#! /usr/bin/env python
# coding: utf-8
#
"""
.. module pygmalion:: 
   :synopsis: turn-based games.

.. moduleauthor: Steven E. Pav <steven@gilgamath.com>

    Created: 2024.05.15
    Copyright: Steven E. Pav, 2024
    Author: Steven E. Pav
    Comments: Steven E. Pav
"""

from abc import ABC, abstractmethod

class AbstractTurnBasedGame(ABC):
    def __init__(self, turn):
        self.__turn = turn

    @property
    @abstractmethod
    def n_players(self):
        pass

    @property
    @abstractmethod
    def valid_moves(self):
        """return list of valid moves"""
        pass

    @property
    def turn(self):
        """which players turn is it?"""
        return self.__turn

    @property
    @abstractmethod
    def winner(self):
        """which player is the winner, or None if game still active."""
        pass

    def _advance(self):
        """advance the player's turn."""
        self.__turn = (self.__turn + 1) % self.n_players

    def _retreat(self):
        """retreat (backtrack, or negative advance) the player's turn."""
        self.__turn = (self.__turn - 1) % self.n_players

    @abstractmethod
    def play(self, move):
        pass

class InvalidMoveException(Exception):
    pass

class TicTacToeGame(AbstractTurnBasedGame):
    __win_indices = [range(0,3), range(3,6), range(6,9), range(0,9,3), range(1,9,3), range(2,9,3), range(0,9,4), range(2,7,2)]
    def __init__(self, turn=0):
        super().__init__(turn=turn)
        self.__board = [" "] * 9
        self.__history = []
        self.__winner = None

    @property
    def winner(self):
        return self.__winner

    @property
    def history(self):
        return self.__history

    @property
    def n_players(self):
        return 2

    @property
    def valid_moves(self):
        if self.winner is not None:
            return []
        else:
            return [idx for idx, spot in enumerate(self.__board) if spot==" "]

    def _check_win(self):
        for wini in self.__win_indices:
            sb = [self.__board[x] for x in wini]
            if all([x=="0" for x in sb]):
                return 0
            elif all([x=="1" for x in sb]):
                return 1
        return None

    def play(self, move):
        if move not in self.valid_moves:
            raise InvalidMoveException
        if self.winner is None:
            self.__board[move] = str(self.turn)
            self.__history.append((self.turn, move))
            # check for win state
            self.__winner = self._check_win()
            if not self.__winner:
                self._advance()

    def backtrack(self):
        if len(self.__history) > 0:
            last_turn, last_move = self.__history.pop()
            self.__board[last_move] = " "
            self._retreat()
            # check for win state
            self.__winner = self._check_win()
            return (last_turn, last_move)
        else:
            return None

    def __repr__(self):
        reps = {"0":" O ","1":" X "," ":"   "}
        breps = [reps[x] for x in self.__board]
        return "|".join(breps[:3]) + "\n" + "|".join(["---"]*3) + "\n" + "|".join(breps[3:6]) + "\n" + "|".join(["---"]*3) + "\n" + "|".join(breps[6:9])




"""
import turn_based as tb
from importlib import reload
reload(tb)
foo = tb.TicTacToeGame()
print(foo)
foo.play(0)
print(foo)
foo.play(1)
print(foo)
foo.backtrack()
print(foo)
foo.backtrack()
print(foo)
foo.backtrack()


print(foo)
foo.play(3)
print(foo)
foo.play(5)
print(foo)
foo.play(6)
print(foo)
foo.winner

foo.backtrack()
foo.play(7)




"""

#for vim modeline: (do not edit)
# vim:ts=4:sw=4:sts=4:tw=79:sta:et:ai:nu:fdm=indent:syn=python:ft=python:tag=.py_tags;:cin:fo=croql
