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
import math
from enum import IntEnum, auto

from dice import FiniteProbabilityDistribution, NumericalFiniteProbabilityDistribution


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

PigRolls = FiniteProbabilityDistribution.from_duplicated(
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
PigPayoff = NumericalFiniteProbabilityDistribution.from_dict(PigPayoff.pmf_dict)

# now a mixed 'dice', which is either 'BACON', or an int value
GamePayoff = NumericalFiniteProbabilityDistribution(
    ["BACON"] + PigPayoff.outcomes,
    [BACON_PROB] + [(1 - BACON_PROB) * x for x in PigPayoff.probabilities],
)



class PassThePigsGame:
    def __init__(self, n_players, turn=0, game_payoff=None, winning_score=100):
        self.__n_players = n_players
        self.__scores = [0] * n_players
        if game_payoff is None:
            game_payoff = NumericalFiniteProbabilityDistribution(
                ["BACON"] + PigPayoff.outcomes,
                [BACON_PROB] + [(1 - BACON_PROB) * x for x in PigPayoff.probabilities],
            )
        self.__winning_score = winning_score
        self.__game_payoff = game_payoff
        self.__turn = turn
        self.__current_tally = 0
        self.__game_winner = None
        self.__turn_history = []

    @property
    def n_players(self):
        return self.__n_players

    @property
    def current_tally(self):
        return self.__current_tally

    @property
    def scores(self):
        return self.__scores

    @property
    def winner(self):
        return self.__game_winner

    @property
    def turn(self):
        return self.__turn

    @property
    def turn_history(self):
        return self.__turn_history

    @property
    def has_tally(self):
        """
        Only True if the current player has rolled and has a tally;
        if the last player has pigged out or made bacon, this is False.
        """
        return self.current_tally != 0

    def __repr__(self):
        as_str = f"{self.scores}\n{self.__turn}'s turn; tally is {self.__current_tally}"
        if self.__game_winner is not None:
            as_str = f"{self.__game_winner} won\n{as_str}"
        return as_str

    def pass_the_pigs(self):
        self.__turn_history.append((self.turn, self.current_tally))
        self.__scores[self.__turn] += self.current_tally
        self.__current_tally = 0
        self.__turn = (self.__turn + 1) % self.n_players

    def roll(self):
        if self.__game_winner is None:
            outcome = self.__game_payoff.generate()
            if outcome == "BACON":
                self.__current_tally = -self.__scores[self.__turn]
                self.pass_the_pigs()
                return -1
            elif outcome == 0:
                self.__current_tally = 0
                self.pass_the_pigs()
                return 0
            else:
                self.__current_tally += outcome
                if (
                    self.__scores[self.__turn] + self.__current_tally
                    >= self.__winning_score
                ):
                    self.__game_winner = self.__turn
                    self.pass_the_pigs()
                    self.__turn = self.__game_winner
                    return 0
                else:
                    return outcome
        else:
            return 0

def normal_cdf(x, lower_tail=True):
    retv = 0.5*(1 + math.erf(x / math.sqrt(2)))
    if lower_tail:
        return retv
    else:
        return 1 - retv


def approximate_chi2_cdf(chi2, df, lower_tail=True):
    """
    Uses the approximation of Luisa Canal (2005)

    """
    adjchi = chi2 / df
    L = adjchi**(1/6) - (1/2) * adjchi**(1/3) + (1/3)*adjchi**(1/2)
    mu = 5/6 - (1/(9*df)) - (7/(648*df*df)) + (25/(2187*df*df*df))
    sigma2 = (1/(18*df)) + (1/(162*df*df)) - (37 / (11664*df*df*df))
    return normal_cdf((L - mu)/math.sqrt(sigma2),lower_tail=lower_tail)

def which_max(a):
    return max(enumerate(a), key=lambda x: x[1])[0]

class PassThePigsTournament:
    def __init__(self, bots, game_payoff=None, winning_score=100):
        self.__bots = bots
        self.__game_payoff = game_payoff
        self.__winning_score = winning_score
        self.__turn = 0
        self.__win_history = [0] * len(bots)

    @property
    def n_players(self):
        return len(self.__bots)

    @property
    def win_history(self):
        return self.__win_history

    @property
    def win_props(self):
        total = sum(self.__win_history)
        return [x/total for x in self.__win_history]

    def play(self, reps):
        for playnum in range(reps):
            new_game = PassThePigsGame(
                n_players=self.n_players,
                turn=self.__turn,
                game_payoff=self.__game_payoff,
                winning_score=self.__winning_score,
            )
            while new_game.winner is None:
                new_game.roll()
                if new_game.has_tally:
                    pturn = new_game.turn
                    scores = copy.copy(new_game.scores)
                    scores = scores[pturn:] + scores[:pturn]
                    do_pass = self.__bots[pturn](
                        new_game.current_tally, scores, self.__winning_score
                    )
                    if do_pass:
                        new_game.pass_the_pigs()
            self.__win_history[new_game.winner] += 1
            self.__turn = (self.__turn + 1) % len(self.__bots)

    def tournament(self, max_reps=10_000, type_I=0.05, type_II=0.20, min_reps=2_000, rep_interval=500):
        """
        Runs some number of rounds of tournaments, then computes a hypothesis test
        for a fair coin. If it finds one strategy dominates the others, it squawks and
        returns. Eventually this will be a proper sequential test.
        """
        found_winner = False
        full_reps = False
        done = False
        winner = None
        while not (found_winner or full_reps):
            self.play(rep_interval)
            observed = self.win_history
            reps = sum(observed)
            expected = [reps/self.n_players] * self.n_players
            # this is twice the negative log likelihood ratio under fair coin.
            G2 = 2 * sum([obs * math.log(obs/expy) for obs,expy in zip(observed, expected)])
            pvalue = approximate_chi2_cdf(G2, self.n_players, lower_tail=False)
            found_winner = (pvalue <= type_I) and (reps >= min_reps)
            winner = which_max(observed)
            full_reps = reps >= max_reps
        if found_winner:
            print(f"{winner} is a winner after {reps} reps. {pvalue=}")
        elif full_reps:
            print(f"no clear winner found after {reps} reps.")
        else:
            print("your code is broken")
        return winner




def run_one(n_matches=50_000):
    fooz = PassThePigsTournament(
        bots=[
            lambda t, s, w: t >= 25,
            lambda t, s, w: t >= 27,
            lambda t, s, w: t >= 30,
        ]
    )
    fooz.play(n_matches)
    print([x / n_matches for x in fooz.win_history])


def run_two(n_matches=10_000):
    fooz = PassThePigsTournament(
        bots=[
            lambda t, s, w: t >= 25,
            lambda t, s, w: t >= 27,
            lambda t, s, w: t >= 30,
            lambda t, s, w: max(s[1:]) < 75 and t >= 28,
        ]
    )
    fooz.play(n_matches)
    print([x / n_matches for x in fooz.win_history])



def run_three(n_matches=10_000):
    fooz = PassThePigsTournament(
        bots=[
            lambda t, s, w: t >= 25,
            lambda t, s, w: t >= 27,
            lambda t, s, w: t >= 30,
            lambda t, s, w: max(s[1:]) < 75 and t >= 28,
        ]
    )
    winner = fooz.tournament(max_reps=n_matches)


# need a sorted product for ordered distributions...
def test_pigroll():
    # TwoPigRolls = PigRolls % copy.deepcopy(PigRolls)
    TwoPigRolls = PigRolls | copy.deepcopy(PigRolls)
    TwoPigRolls.generate()
    TwoPigRolls.pmf_dict


def test_pig_payoff():
    ep = PigPayoff.expected_value()
    vp = PigPayoff.variance()


def test_pig_game():
    startit = PassThePigsGame(n_players=2)
    while startit.winner is None:
        startit.pass_the_pigs()
        startit.roll()
        startit.roll()


# for vim modeline: (do not edit)
# vim:ts=4:sw=4:sts=4:tw=79:sta:et:ai:nu:fdm=indent:syn=python:ft=python:tag=.py_tags;:cin:fo=croql
