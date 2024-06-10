#! /usr/bin/env python
# coding: utf-8
#
"""
.. module pygmalion:: pygmalion
   :synopsis: analysis of the card game 'put'

.. moduleauthor: Steven E. Pav <steven@gilgamath.com>

    SVN: $Id$
    Created: 2024.06.09
    Copyright: Steven E. Pav, 2024
    Author: Steven E. Pav
    Comments: Steven E. Pav
"""

import itertools
from math import factorial, comb

def _score_trick(play1, play2):
    """
    +/-1 or 0 from player 1's perspective.
    """
    return 1 if play1 > play2 else (-1 if play1 < play2 else 0)

def _score_match(trick1, trick2, trick3):
    """
    the trick scores are from player 1's perspective; 
    sum them to a match win/loss from player 1's perspective.
    """
    if trick1 > 0:
        if max(trick2, trick3) > 0:
            return 1
        elif max(trick2, trick3) < 0:
            return -1
        else:
            return 0
    elif trick1 < 0:
        if min(trick2, trick3) < 0:
            return -1
        elif min(trick2, trick3) > 0:
            return 1
        else:
            return 0
    else:
        if min(trick2, trick3) > 0:
            return 1
        elif max(trick2, trick3) < 0:
            return -1
        else:
            return 0


def second_trick_follower_value():
    """
    computes a dict which is keyed by [(unplayed1, myplayed1, myplayed2, theirplayed1, theirplayed2)] with value
    the conditional expected match value from 'my' POV.
    the expected value is _conditional_ on those cards having been played.
    """
    secf = {}
    for myun1, mypl1, mypl2, thpl1, thpl2 in itertools.product(range(13), repeat=5):
        unpl = [4] * 13
        unpl[myun1] -= 1
        unpl[mypl1] -= 1
        unpl[mypl2] -= 1
        unpl[thpl1] -= 1
        unpl[thpl2] -= 1
        if min(unpl) >= 0:
            first_trick = _score_trick(mypl1, thpl1)
            second_trick = _score_trick(mypl2, thpl2)
            deno = 0
            numr = 0
            for thun1, wt in enumerate(unpl):
                third_trick = _score_trick(myun1, thun1)
                numr += wt * _score_match(first_trick, second_trick, third_trick)
                deno += wt
            secf[(myun1, mypl1, mypl2, thpl1, thpl2)] = numr / deno
    return secf

def second_trick_follower_decision(secf=None):
    """
    computes a dict which is keyed by [(unplayed1, unplayed2, myplayed1, theirplayed1, theirplayed2)] with value
    the optimal conditional expected match value from 'my' POV, and the card to play from my two unplayed cards.
    by convention unplayed1 >= unplayed2
    the expected value is _conditional_ on those cards having been played.
    """
    if secf is None:
        secf = second_trick_follower_value()
    secfd = {}
    for myun1, myun2, mypl1, thpl1, thpl2 in itertools.product(range(13), repeat=5):
        if myun1 < myun2:
            continue
        val1 = secf.get((myun2, mypl1, myun1, thpl1, thpl2), None)
        if val1 is None:
            continue
        val2 = secf.get((myun1, mypl1, myun2, thpl1, thpl2))
        secfd[(myun1, myun2, mypl1, thpl1, thpl2)] = max([(val1, myun1), (val2, myun2)])
    return secfd

secf = second_trick_follower_value()
secfd = second_trick_follower_decision(secf)

# compute how many ways you could draw from a given number of urns, without
# replacement. This is a multinomial coefficient?
def _comp_wt(urn_counts, *args):
    dups = [0] * len(urn_counts)
    for apick in [*args]:
        dups[apick] += 1
    wt = 1
    for idx, ntake in enumerate(dups):
        wt *= comb(urn_counts[idx], ntake)
    return wt

def second_trick_leader_value(secfd=None):
    """
    computes a dict which is keyed by [(unplayed1, myplayed1, myplayed2, theirplayed1)] with value
    the conditional expected match value from 'my' POV of leading with myplayed2 in the second
    trick. 
    the expected value is _conditional_ on those cards having been played, and on the opponent
    playing the optimal follow decision.
    By assumption since I am leading in the second trick, myplayed1 >= theirplayed1.
    """
    if secfd is None:
        secfd = second_trick_follower_decision()
    secl = {}
    for myun1, mypl1, mypl2, thpl1 in itertools.product(range(13), repeat=4):
        if mypl1 < thpl1:
            continue
        unpl = [4] * 13
        unpl[myun1] -= 1
        unpl[mypl1] -= 1
        unpl[mypl2] -= 1
        unpl[thpl1] -= 1
        if min(unpl) >= 0:
            first_trick = _score_trick(mypl1, thpl1)
            deno = 0
            numr = 0
            for thun1, thun2 in itertools.product(range(13), repeat=2):
                wt = _comp_wt(unpl, thun1, thun2)
                if wt <= 0:
                    continue
                # figure out what they follow with:
                _, thpl2 = secfd[(max(thun1, thun2), min(thun1, thun2), thpl1, mypl1, mypl2)]
                second_trick = _score_trick(mypl2, thpl2)
                thpl3 = thun2 if thpl2==thun1 else thun1
                third_trick = _score_trick(myun1, thpl3)
                numr += wt * _score_match(first_trick, second_trick, third_trick)
                deno += wt
            secl[(myun1, mypl1, mypl2, thpl1)] = numr / deno
    return secl

def second_trick_leader_decision(secl=None):
    """
    computes a dict which is keyed by [(unplayed1, unplayed2, myplayed1, theirplayed1)] with value
    the conditional expected match value from 'my' POV, and the optimal card to lead with in the second trick.
    the expected value is _conditional_ on those cards having been played, and on the opponent
    playing the optimal follow decision.
    By assumption since I am leading in the second trick, myplayed1 >= theirplayed1.
    We also assume unplayed1 >= unplayed2
    """
    if secl is None:
        secl = second_trick_leader_value()
    secld = {}
    for myun1, myun2, mypl1, thpl1 in itertools.product(range(13), repeat=4):
        if myun1 < myun2:
            continue
        if mypl1 < thpl1:
            continue
        val1 = secl.get((myun2, mypl1, myun1, thpl1), None)
        if val1 is None:
            continue
        val2 = secl.get((myun1, mypl1, myun2, thpl1))
        secld[(myun1, myun2, mypl1, thpl1)] = max([(val1, myun1), (val2, myun2)])
    return secld




secf = second_trick_follower_value()
secfd = second_trick_follower_decision(secf)
secl = second_trick_leader_value(secfd)
secld = second_trick_leader_decision(secl)

def first_trick_follower_value(secld=None):
    """
    computes a dict which is keyed by [(unplayed1, unplayed2, myplayed1, theirplayed1)] with value
    the conditional expected match value from 'my' POV of following in the first trick with myplayed1.
    the expected value is _conditional_ on those cards having been played, and everyone playing the optimal
    decisions.
    By assumption unplayed1 >= unplayed2
    """
    if secld is None:
        secld = second_trick_leader_decision()
    firf = {}
    for myun1, mypl1, mypl2, thpl1 in itertools.product(range(13), repeat=4):
        # now what?
        pass


#for vim modeline: (do not edit)
# vim:ts=4:sw=4:sts=4:tw=79:sta:et:ai:nu:fdm=indent:syn=python:ft=python:tag=.py_tags;:cin:fo=croql
