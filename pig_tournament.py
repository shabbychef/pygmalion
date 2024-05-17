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
from collections import defaultdict

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

# winprobs is a dict with keys as tuples:
# (myscore, theirscore, mytally) and points to (probwin, best_action)
# we prepopulate it with approximate winprobs.
winprobs = defaultdict(lambda : (0.5, None))  # not sure this is necessary
winscore = 100
for myscore in range(winscore):
    for theirscore in range(winscore):
        for tally in range(winscore-myscore):
            probwin = 0.03 + (0.5 * (1 + ((myscore + tally) - theirscore) / winscore))
            probwin += 0.3 * (myscore+tally)/winscore
            probwin = max(0,min(1,probwin))
            winprobs[(myscore, theirscore, tally)] = (probwin, None)

def do_dp_updates(winprobs, other_probs=None, min_change=0.002, max_it=100, sentinel_keys=[(0,0,0), (30,30,0), (91,91,1)]):
    if other_probs is None:
        other_probs = pig.GamePayoff.pmf_dict
    bacon_prob = other_probs['BACON']
    zero_prob = other_probs[0]
    del other_probs['BACON']
    del other_probs[0]
    sentinel = {key:winprobs[key][0] for key in sentinel_keys}
    iterates = 0
    done_iterates = iterates >= max_it
    converged = False
    while not done_iterates and not converged:
        for myscore in range(winscore,-1,-1):
            for theirscore in range(winscore,-1,-1):
                for tally in range(winscore-myscore,-1,-1):
                    pass_lose_prob, _ = winprobs[(theirscore, myscore+tally, 0)]
                    pass_win_prob = 1 - pass_lose_prob
                    # now the probability of winning when you roll again.
                    roll_win_prob = 0
                    bacon_lose_prob, _ = winprobs[(theirscore, 0, 0)] 
                    roll_win_prob += bacon_prob * (1 - bacon_lose_prob)
                    pigout_lose_prob, _ = winprobs[(theirscore, myscore, 0)] 
                    roll_win_prob += zero_prob * (1 - pigout_lose_prob)
                    for points, prob in other_probs.items():
                        if myscore + tally + points >= winscore:
                            this_win_prob = 1
                        else:
                            this_win_prob, _ = winprobs[(myscore, theirscore, tally + points)] 
                        roll_win_prob += prob * this_win_prob
                    # we now have the pass_win_prob and the roll_win_prob; use these.
                    if pass_win_prob > roll_win_prob:
                        winprobs[(myscore, theirscore, tally)] = (pass_win_prob, 'pass')
                    else:
                        winprobs[(myscore, theirscore, tally)] = (roll_win_prob, 'roll')
        iterates += 1
        done_iterates = iterates >= max_it
        next_sentinel = {key:winprobs[key][0] for key in sentinel_keys}
        converged = max([abs(next_sentinel[key] - value) for key, value in sentinel.items()]) < min_change
        print(f"{iterates=} {sentinel=} {next_sentinel=}")
        sentinel = next_sentinel
    return winprobs

winprobs = do_dp_updates(winprobs, min_change=0.0001, max_it=100)

for k,v in winprobs.items():
    if v[1] is None:
        print(f"missing for {k}")
        break

def strategy_optimal(tally, scores, winscore, winprobs):
    myscore = scores[0]
    theirscore = max(scores[1:])
    _, strat = winprobs[(myscore, theirscore, tally)]
    return strat == "pass"

def example_tournament_3(max_reps=10_000):
    tourney = pig.PassThePigsTournament(
        bots=[
            functools.partial(strategy_tally_limit, tally_limit=32),
            functools.partial(strategy_optimal, winprobs=winprobs),
            strategy_weird,
            strategy_expected_value_limit,
        ]
    )
    winner = tourney.tournament(max_reps=max_reps, min_reps=0.5 * max_reps)
    return tourney

tourney = example_tournament_3(50_000)
tourney.win_history


#for vim modeline: (do not edit)
# vim:ts=4:sw=4:sts=4:tw=79:sta:et:ai:nu:fdm=indent:syn=python:ft=python:tag=.py_tags;:cin:fo=croql
