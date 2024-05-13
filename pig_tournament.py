#! /usr/bin/env python
# coding: utf-8
#
"""
.. module pygmalion:: games and such
   :synopsis: Pass the Pigs tournament

.. moduleauthor: Steven E. Pav <steven@gilgamath.com>

    Created: 2024.05.12
    Copyright: Steven E. Pav, 2024
    Author: Steven E. Pav
    Comments: Steven E. Pav
"""

import pig
import functools

def strategy_tally_limit(tally, scores, winscore, tally_limit=20):
    return tally >= tally_limit

exp_payoff = pig.PigPayoff.expected_value() 
prob_pigout = pig.PigPayoff.pmf(0) 

def strategy_expected_value_limit(tally, scores, winscore, bacon_prob=None, exp_payoff=None, prob_pigout=None):
    if bacon_prob is None:
        bacon_prob = pig.GamePayoff.pmf('BACON') 
    if prob_pigout is None:
        prob_pigout = pig.GamePayoff.pmf(0)
    if exp_payoff is None:
        pd = pig.GamePayoff.pmf_dict
        exp_payoff = 0
        for k, v in pd.items():
            if isinstance(k, (int,float)):
                exp_payoff += k*v
    # the expected value from another roll is
    exp_another_roll = exp_payoff - tally * (prob_pigout) - (tally + scores[0]) * bacon_prob
    return exp_another_roll <= 0

def strategy_weird(tally, scores, winscore):
    return max(scores[1:]) < 75 and tally >= 28


strategy_expected_value_limit(15, [40, 0, 0, 0], 100)
strategy_expected_value_limit(21, [40, 0, 0, 0], 100)
strategy_expected_value_limit(21, [80, 0, 0, 0], 100)

def example_tournament_1(max_reps=10_000):
    tourney = pig.PassThePigsTournament(
        bots=[
            functools.partial(strategy_tally_limit, tally_limit=25),
            functools.partial(strategy_tally_limit, tally_limit=27),
            functools.partial(strategy_tally_limit, tally_limit=30),
            functools.partial(strategy_tally_limit, tally_limit=32),
            functools.partial(strategy_tally_limit, tally_limit=34),
            functools.partial(strategy_tally_limit, tally_limit=36),
            functools.partial(strategy_tally_limit, tally_limit=38),
        ]
    )
    winner = tourney.tournament(max_reps=max_reps)

def example_tournament_2(max_reps=10_000):
    tourney = pig.PassThePigsTournament(
        bots=[
            functools.partial(strategy_tally_limit, tally_limit=32),
            strategy_weird,
            strategy_expected_value_limit,
        ]
    )
    winner = tourney.tournament(max_reps=max_reps)
    return tourney

tourney = example_tournament_2(40_000)
tourney.win_history

#for vim modeline: (do not edit)
# vim:ts=4:sw=4:sts=4:tw=79:sta:et:ai:nu:fdm=indent:syn=python:ft=python:tag=.py_tags;:cin:fo=croql
