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

import random
from abc import ABC, abstractmethod

class AbstractSequentialGame(ABC):
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
        """
        Which player is the winner, or None if game still active.
        By assumption, if there is a winner, then that player played the last move.
        """
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

class HistoryMixin():
    @property
    @abstractmethod
    def history(self):
        pass

    @property
    def ply(self):
        return len(self.history)

class StateMixin():
    @property
    @abstractmethod
    def state_string(self):
        """
        A string based representation of the game, without history.
        2FIX: should have a method to re-hydrate the game from the state_string? but without history?
        """
        pass

class InvalidMoveException(Exception):
    pass

class TicTacToeGame(StateMixin, HistoryMixin, AbstractSequentialGame):
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
    def state_string(self):
        return f"{self.turn}:" + ("".join(self.__board))

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

class ConnectFourGame(StateMixin, HistoryMixin, AbstractSequentialGame):
    def __init__(self, n_connect=4, n_players=2, width=7, height=6, turn=0):
        super().__init__(turn=turn)
        self.__n_players = n_players
        self.__board = [" "] * width * height
        self.__history = []
        self.__n_connect = n_connect
        self.__width = width
        self.__height = height
        win_indices = []
        maxi = width * height
        # horizontal win indices
        for rown in range(height):
            for coln in range(1+width-n_connect):
                idx = rown*width + coln
                idx_end = idx + n_connect
                win_indices.append(range(idx,idx_end))
        # vertical win indices
        for rown in range(1+height-n_connect):
            for coln in range(width):
                idx = rown*width + coln
                idx_end = (rown+n_connect)*width + coln
                win_indices.append(range(idx,idx_end,width))
        # up diagonal win indices
        for rown in range(1+height-n_connect):
            for coln in range(1+width-n_connect):
                idx = rown*width + coln
                idx_end = (rown+n_connect)*width + coln + n_connect
                win_indices.append(range(idx,idx_end,width+1))
        # down diagonal win indices
        for rown in range(1+height-n_connect):
            for coln in range(n_connect-1,width):
                idx = rown*width + coln
                idx_end = (rown+n_connect)*width + coln - n_connect
                win_indices.append(range(idx,idx_end,width-1))
        self.__win_indices = win_indices
        self.__winner = None

    @property
    def win_indices(self):
        return self.__win_indices

    @property
    def winner(self):
        return self.__winner

    @property
    def history(self):
        return self.__history

    @property
    def state_string(self):
        return f"{self.__width},{self.__height},{self.__n_connect},{self.__n_players},{self.turn}:" + ("".join(self.__board))

    @property
    def shape(self):
        return (self.__width, self.__height)

    @property
    def n_players(self):
        return self.__n_players

    def _check_win(self):
        for wini in self.__win_indices:
            sb = [self.__board[x] for x in wini]
            if sb[0] != " " and all([x==sb[0] for x in sb[1:]]):
                return int(sb[0])
        return None

    @property
    def valid_moves(self):
        if self.winner is not None:
            return []
        else:
            return [idx for idx, spot in enumerate(self.__board[((self.__height-1)*self.__width):]) if spot==" "]

    def _check_win(self):
        for wini in self.__win_indices:
            sb = [self.__board[x] for x in wini]
            if all([x=="0" for x in sb]):
                return 0
            elif all([x=="1" for x in sb]):
                return 1
        return None

    def play(self, move):
        if move not in self.valid_moves or move is None:
            raise InvalidMoveException
        if self.winner is None:
            rown = 0
            while self.__board[rown*self.__width+move] != " ":
                rown += 1
            self.__board[rown*self.__width+move] = str(self.turn)
            self.__history.append((self.turn, move))
            # check for win state
            self.__winner = self._check_win()
            if not self.__winner:
                self._advance()

    def backtrack(self):
        if len(self.__history) > 0:
            last_turn, last_move = self.__history.pop()
            rown = self.__height-1
            while self.__board[rown*self.__width+last_move] == " ":
                rown -= 1
            self.__board[rown*self.__width+last_move] = " "
            self._retreat()
            # check for win state; probably safe to just set to None.
            self.__winner = self._check_win()
            return (last_turn, last_move)
        else:
            return None

    def __repr__(self):
        bs = ""
        for idx in range(self.__height-1,-1,-1):
            bs += "|" + "|".join(self.__board[(self.__width*idx):(self.__width*(idx+1))])
            bs += "|\n"
        return bs


# can play any multiplayer game.
def random_player(gameboard: AbstractSequentialGame):
    return random.choices(gameboard.valid_moves, k=1)[0]

def likes_center_player(gameboard: ConnectFourGame):
    vm = gameboard.valid_moves
    wid = gameboard.shape[0]
    minv = [(abs(v-(wid-1)/2),v) for v in vm]
    return min(minv)[1]

def simple_lookahead(gameboard: ConnectFourGame):
    whoami = gameboard.turn
    vm = gameboard.valid_moves
    for move in vm:
        gameboard.play(move)
        if gameboard.winner is not None:
            gameboard.backtrack()
            return move
        gameboard.backtrack()
    # no winning moves.
    return random.choices(vm, k=1)[0]


# this almost works for any Sequential game with backtrack?
def _alpha_beta_search(gameboard: ConnectFourGame, alpha:float=-1, beta:float=1, depth:int=2):
    # this is flawed; turn should be zero if winner state is not None. Rats.
    whoami = gameboard.turn
    if gameboard.winner is not None:
        return (-10, None)
    elif depth <= 0:
        vm = gameboard.valid_moves
        if len(vm):
            # return a valid move?
            return (0, vm[0])
        else:
            return (0.2, None)
    else:
        vm = gameboard.valid_moves
        if gameboard.ply == 0:
            # abuse symmetry
            upto = (max(vm) + 1)//2
            vm = [v for v in vm if v <= upto]
        random.shuffle(vm)
        if len(vm):
            whatifs = []
            for move in vm:
                gameboard.play(move)
                theirvalue, _ = _alpha_beta_search(gameboard, alpha=-beta, beta=-alpha, depth=depth-1)
                gameboard.backtrack()
                value = -0.9*theirvalue + (0.0001 * random.random())
                if value > beta:
                    return (value, move)
                else:
                    alpha = max(alpha, value)
                whatifs.append((value, move))
            return max(whatifs)
        else:
            return (0, None)

# this almost works for any Sequential game with backtrack?
def _alpha_beta_search(gameboard: ConnectFourGame, alpha:float=-1, beta:float=1, depth:int=2, memo_pad=None):
    memo_pad = memo_pad or {}
    game_key = gameboard.state_string
    if game_key in memo_pad:
        return memo_pad[game_key]
    
    if gameboard.winner is not None:
        memo_pad[game_key] = (-10, None)
        return (-10, None)
    elif depth <= 0:
        vm = gameboard.valid_moves
        if len(vm):
            # return a valid move?
            memo_pad[game_key] = (0, vm[0])
            return (0, vm[0])
        else:
            memo_pad[game_key] = (0.2, None)
            return (0.2, None)
    else:
        vm = gameboard.valid_moves
        if gameboard.ply == 0:
            # abuse symmetry
            upto = (max(vm) + 1)//2
            vm = [v for v in vm if v <= upto]
        random.shuffle(vm)
        if len(vm):
            whatifs = []
            for move in vm:
                gameboard.play(move)
                theirvalue, _ = _alpha_beta_search(gameboard, alpha=-beta, beta=-alpha, depth=depth-1, memo_pad=memo_pad)
                gameboard.backtrack()
                value = -0.9*theirvalue + (0.0001 * random.random())
                if value > beta:
                    memo_pad[game_key] = (value, move)
                    return (value, move)
                else:
                    alpha = max(alpha, value)
                whatifs.append((value, move))
            memo_pad[game_key] = max(whatifs)
            return max(whatifs)
        else:
            memo_pad[game_key] = (0, None)
            return (0, None)

def complex_lookahead(gameboard: ConnectFourGame, depth=9):
    return _alpha_beta_search(gameboard, depth=depth)[1]


def mid_lookahead(gameboard: ConnectFourGame, depth=5):
    return _alpha_beta_search(gameboard, depth=depth)[1]


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


reload(tb)
baz = tb.ConnectFourGame()
[list(x) for x in baz.win_indices]
print(baz)
baz.valid_moves
baz.play(0)
print(baz)
baz.play(1)
print(baz)
baz.play(2)


import turn_based as tb
reload(tb)
baz = tb.ConnectFourGame()
while baz.winner is None:
    move = random_player(baz)
    print(f"{baz.turn} plays {move}")
    baz.play(move)
    print(baz)

baz = tb.ConnectFourGame()
while baz.winner is None:
    move = likes_center_player(baz)
    print(f"{baz.turn} plays {move}")
    baz.play(move)
    print(baz)
    move = random_player(baz)
    print(f"{baz.turn} plays {move}")
    baz.play(move)
    print(baz)

from copy import deepcopy

def playem(bots_list,turn=0):
    gameboard = tb.ConnectFourGame(n_players=len(bots_list),turn=turn)
    while gameboard.winner is None and len(gameboard.valid_moves) > 0:
        print(f"the turn is for {gameboard.turn}")
        move = bots_list[gameboard.turn](deepcopy(gameboard))
        print(f"{gameboard.turn} plays {move}")
        gameboard.play(move)
        print(gameboard)
    return gameboard.winner


playem([random_player, random_player, likes_center_player])
playem([random_player, simple_lookahead])
playem([complex_lookahead, simple_lookahead])
playem([complex_lookahead, random_player])
playem([complex_lookahead, complex_lookahead])
playem([complex_lookahead, mid_lookahead, random_player])
playem([mid_lookahead, mid_lookahead, random_player])

gameboard = tb.ConnectFourGame(n_players=2,turn=0)
complex_lookahead(gameboard)
    
# playem([random_player])
gameboard = tb.ConnectFourGame(n_players=2,turn=0)
gameboard.play(0)
gameboard.play(1)
gameboard.play(2)
gameboard.play(1)
gameboard.play(3)
gameboard.play(1)
gameboard.play(4)
print(gameboard)
_alpha_beta_search(gameboard)

complex_lookahead(gameboard)

"""

#for vim modeline: (do not edit)
# vim:ts=4:sw=4:sts=4:tw=79:sta:et:ai:nu:fdm=indent:syn=python:ft=python:tag=.py_tags;:cin:fo=croql
