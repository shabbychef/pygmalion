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
from math import factorial, comb, perm
from collections import Counter


def urn_perm(aco: Counter, k:int=1):
    """
    A generator over k-tuples of elements selected without replacement from the given counts.
    This is a permutation generator, so the order matters.
    """
    total_count = sum(aco.values())
    assert k <= total_count, f"cannot permute {k=} objects from {total_count}"
    deno = perm(total_count, k)
    for atup in itertools.product(aco.keys(), repeat=k):
        wt = 1
        acop = dict(aco).copy()
        for av in atup:
            wt *= acop[av]
            acop[av] -= 1
        if wt != 0:
            yield (*atup, wt/deno)


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

def _score_match_from(mypl1, mypl2, mypl3, thpl1, thpl2, thpl3):
    return _score_match(_score_trick(mypl1, thpl1), _score_trick(mypl2, thpl2), _score_trick(mypl3, thpl3))

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
            aco = Counter(dict(list(enumerate(unpl))))
            for thun1, wt in urn_perm(aco, 1):
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
            aco = Counter(dict(list(enumerate(unpl))))
            numr = 0
            deno = 0
            for thun1, thun2, wt in urn_perm(aco, 2):
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


# ideally there would be an iterator for selecting k cards from a series of n
# cards, along with the relative probability weight!

secf = second_trick_follower_value()
secfd = second_trick_follower_decision(secf)
secl = second_trick_leader_value(secfd)
secld = second_trick_leader_decision(secl)
# uninit'd
secld = second_trick_leader_decision()

def first_trick_follower_value(secld=None, secfd=None):
    """
    computes a dict which is keyed by [(unplayed1, unplayed2, myplayed1, theirplayed1)] with value
    the conditional expected match value from 'my' POV of following in the first trick with myplayed1.
    the expected value is _conditional_ on those cards having been played, and everyone playing the optimal
    decisions.
    By assumption unplayed1 >= unplayed2
    """
    if secld is None:
        secld = second_trick_leader_decision()
    if secfd is None:
        secfd = second_trick_follower_decision()
    firf = {}
    for myun1, myun2, mypl1, thpl1 in itertools.product(range(13), repeat=4):
        if myun1 < myun2:
            continue
        unpl = [4] * 13
        unpl[myun1] -= 1
        unpl[myun2] -= 1
        unpl[mypl1] -= 1
        unpl[thpl1] -= 1
        if min(unpl) >= 0:
            first_trick = _score_trick(mypl1, thpl1)
            aco = Counter(dict(list(enumerate(unpl))))
            numr = 0
            deno = 0
            for thun1, thun2, wt in urn_perm(aco, 2):
                if wt <= 0:
                    continue
                if first_trick > 0:
                    # we lead in the second trick
                    # what should we lead with?
                    _, mypl2 = secld[(max(myun1, myun2), min(myun1, myun2), mypl1, thpl1)]
                    # what should they follow in the second trick with?
                    _, thpl2 = secfd[(max(thun1, thun2), min(thun1, thun2), thpl1, mypl1, mypl2)]
                else:
                    # first trick we tied or lost after following, so we follow
                    # in the second.
                    # figure out what they would lead with
                    _, thpl2 = secld[(max(thun1, thun2), min(thun1, thun2), thpl1, mypl1)]
                    # what should we follow with in the second trick?
                    _, mypl2 = secfd[(max(myun1, myun2), min(myun1, myun2), mypl1, thpl1, thpl2)]
                mypl3 = myun1 if mypl2 == myun2 else myun2
                thpl3 = thun1 if thpl2 == thun2 else thun2
                second_trick = _score_trick(mypl2, thpl2)
                third_trick = _score_trick(mypl3, thpl3)
                numr += wt * _score_match(first_trick, second_trick, third_trick)
                deno += wt
        firf[(myun1, myun2, mypl1, thpl1)] = numr / deno
    return firf

firf = first_trick_follower_value(secld, secfd)

def first_trick_follower_decision(firf=None):
    """
    computes a dict which is keyed by [(unplayed1, unplayed2, unplayed3, theirplayed1)] with value
    the conditional expected match value from 'my' POV of following in the first trick, and the optimal card to play.
    the expected value is _conditional_ on those cards having been played, and everyone playing the optimal
    decisions.
    By assumption unplayed1 >= unplayed2 and unplayed2 >= unplayed3
    """
    if firf is None:
        firf = first_trick_follower_value()
    firfd = {}
    for myun1, myun2, myun3, thpl1 in itertools.product(range(13), repeat=4):
        if (myun1 < myun2) or (myun2 < myun3):
            continue
        # value from playing 1, 2 or 3
        val1 = firf[(myun2, myun3, myun1, thpl1)]
        val2 = firf[(myun1, myun3, myun2, thpl1)]
        val3 = firf[(myun1, myun2, myun3, thpl1)]
        firfd[(myun1, myun2, myun3, thpl1)] = max([(val1, myun1), (val2, myun2), (val3, myun3)])
    return firfd

firfd = first_trick_follower_decision(firf)

# now the first trick leader value.
def first_trick_leader_value(firfd=None, secld=None, secfd=None):
    """
    computes a dict which is keyed by [(unplayed1, unplayed2, myplayed1)] with value
    the conditional expected match value from 'my' POV of following in the first trick with myplayed1.
    the expected value is _conditional_ on those cards having been played, and everyone playing the optimal
    decisions.
    By assumption unplayed1 >= unplayed2
    """
    if secld is None:
        secld = second_trick_leader_decision()
    if secfd is None:
        secfd = second_trick_follower_decision()
    if firfd is None:
        firf = first_trick_follower_value(secld, secfd)
        firfd = first_trick_follower_decision(firf)
    firl = {}
    for myun1, myun2, mypl1 in itertools.product(range(13), repeat=3):
        if myun1 < myun2:
            continue
        unpl = [4] * 13
        unpl[myun1] -= 1
        unpl[myun2] -= 1
        unpl[mypl1] -= 1
        aco = Counter(dict(list(enumerate(unpl))))
        numr = 0
        deno = 0
        for thun1, thun2, thun3, wt in urn_perm(aco, 3):
            if wt <= 0:
                continue
            sord = sorted([thun1, thun2, thun3], reverse=True)
            _, thpl1 = firfd[(*sord, mypl1)]
            first_trick = _score_trick(mypl1, thpl1)
            # get their unplayed cards.
            if thpl1 == thun1:
                threm1, threm2 = (max(thun2, thun3), min(thun2, thun3))
            elif thpl1 == thun2:
                threm1, threm2 = (max(thun1, thun3), min(thun1, thun3))
            else:
                threm1, threm2 = (max(thun1, thun2), min(thun1, thun2))
            # depending on who wins first trick we have different leader/follower in second.
            if first_trick >= 0:
                # win or tie, I lead again
                _, mypl2 = secld[(myun1, myun2, mypl1, thpl1)]
                # their response is:
                _, thpl2 = secfd[(threm1, threm2, thpl1, mypl1, mypl2)]
            else:
                # they lead.
                _, thpl2 = secld[(threm1, threm2, thpl1, mypl1)]
                # my response should be
                _, mypl2 = secfd[(myun1, myun2, mypl1, thpl1, thpl2)]
                pass
            mypl3 = myun1 if mypl2 == myun2 else myun2
            thpl3 = threm1 if thpl2 == threm2 else threm2
            second_trick = _score_trick(mypl2, thpl2)
            third_trick = _score_trick(mypl3, thpl3)
            numr += wt * _score_match(first_trick, second_trick, third_trick)
            deno += wt
        firl[(myun1, myun2, mypl1)] = numr / deno
    return firl

# now the first trick leader decision.
def first_trick_leader_decision(firl=None):
    """
    computes a dict which is keyed by [(unplayed1, unplayed2, unplayed3)] with value
    the conditional expected match value from 'my' POV of following in the first trick with myplayed1, and the optimal move.
    the expected value is _conditional_ on those cards having been played, and everyone playing the optimal
    decisions.
    By assumption unplayed1 >= unplayed2 >= unplayed3
    """
    if firl is None:
        firl = first_trick_leader_value()
    firld = {}
    for myun1, myun2, myun3 in itertools.product(range(13), repeat=3):
        if (myun1 < myun2) or (myun2 < myun3):
            continue
        # value from playing 1, 2 or 3
        val1 = firl[(myun2, myun3, myun1)]
        val2 = firl[(myun1, myun3, myun2)]
        val3 = firl[(myun1, myun2, myun3)]
        firld[(myun1, myun2, myun3)] = max([(val1, myun1), (val2, myun2), (val3, myun3)])
    return firld

firl = first_trick_leader_value(firfd, secld, secfd)

# now the first trick leader value.
firld = first_trick_leader_decision(firl)

#for vim modeline: (do not edit)
# vim:ts=4:sw=4:sts=4:tw=79:sta:et:ai:nu:fdm=indent:syn=python:ft=python:tag=.py_tags;:cin:fo=croql
