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

"""
You need to do the scoring for the score of each participant.
Which is to say for the scores 0-0 through 4-4, which is a grid of 25!
At 4-4, there is no reason to call Put, as your opponent must always accept.
But even at 4-4, where there is no possibility of Put, there is the probability of a tie,
after which play resumes with a new deal.
So if p is your probability of winning, without viewing your cards, at the beginning of a 4-4 match,
there is some recursion with 
p = p1 + p2 * (p1 + p2 * (p1 + p2 * (...)))
where p1 is the unconditional probability of wining outright from a given position and
p2 is the unconditional probability of a tie.
"""

from urn import Urn

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


def second_trick_follower_value(deck: Urn):
    """
    computes a dict which is keyed by [(unplayed1, myplayed1, myplayed2, theirplayed1, theirplayed2)] with value
    the conditional expected match value from 'my' POV.
    the expected value is _conditional_ on those cards having been played.
    """
    secf = {}
    for myun1, mypl1, mypl2, thpl1, thpl2, ignore_wt, tail_urn in deck.perm_k(k=5):
        first_trick = _score_trick(mypl1, thpl1)
        second_trick = _score_trick(mypl2, thpl2)
        deno = 0
        numr = 0
        for thun1, wt, _ in tail_urn.perm_k(k=1):
            third_trick = _score_trick(myun1, thun1)
            numr += wt * _score_match(first_trick, second_trick, third_trick)
            deno += wt
        secf[(myun1, mypl1, mypl2, thpl1, thpl2)] = numr / deno
    return secf

def second_trick_follower_decision(deck: Urn, secf=None):
    """
    computes a dict which is keyed by [(unplayed1, unplayed2, myplayed1, theirplayed1, theirplayed2)] with value
    the optimal conditional expected match value from 'my' POV, and the card to play from my two unplayed cards.
    by convention unplayed1 >= unplayed2
    the expected value is _conditional_ on those cards having been played.
    """
    if secf is None:
        secf = second_trick_follower_value(deck=deck)
    secfd = {}
    for myun1, myun2, mypl1, thpl1, thpl2, ignore_wt, tail_urn in deck.perm_k(k=5):
        if myun1 < myun2:
            continue
        val1 = secf.get((myun2, mypl1, myun1, thpl1, thpl2), None)
        if val1 is None:
            continue
        val2 = secf.get((myun1, mypl1, myun2, thpl1, thpl2))
        secfd[(myun1, myun2, mypl1, thpl1, thpl2)] = max([(val1, myun1), (val2, myun2)])
    return secfd

master_deck = Urn(Counter({k:4 for k in range(13)}) + Counter({13:2}))
secf = second_trick_follower_value(deck=master_deck)
secfd = second_trick_follower_decision(deck=master_deck,secf)

short_deck = Urn(Counter({k:4 for k in range(5)}))
secf = second_trick_follower_value(short_deck)
secfd = second_trick_follower_decision(short_deck,secf)


def second_trick_leader_value(deck:Urn, secfd=None):
    """
    computes a dict which is keyed by [(unplayed1, myplayed1, myplayed2, theirplayed1)] with value
    the conditional expected match value from 'my' POV of leading with myplayed2 in the second
    trick. 
    the expected value is _conditional_ on those cards having been played, and on the opponent
    playing the optimal follow decision.
    By assumption since I am leading in the second trick, myplayed1 >= theirplayed1.
    """
    if secfd is None:
        secfd = second_trick_follower_decision(deck)
    secl = {}
    for myun1, mypl1, mypl2, thpl1, ignore_wt, tail_urn in deck.perm_k(k=4):
        if mypl1 < thpl1:
            continue
        first_trick = _score_trick(mypl1, thpl1)
        numr = 0
        deno = 0
        for thun1, thun2, wt, _ in tail_urn.perm_k(k=2):
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

secl = second_trick_leader_value(short_deck, secfd)

def second_trick_leader_decision(deck:Urn, secl=None):
    """
    computes a dict which is keyed by [(unplayed1, unplayed2, myplayed1, theirplayed1)] with value
    the conditional expected match value from 'my' POV, and the optimal card to lead with in the second trick.
    the expected value is _conditional_ on those cards having been played, and on the opponent
    playing the optimal follow decision.
    By assumption since I am leading in the second trick, myplayed1 >= theirplayed1.
    We also assume unplayed1 >= unplayed2
    """
    if secl is None:
        secl = second_trick_leader_value(deck)
    secld = {}
    for myun1, myun2, mypl1, thpl1, _, _ in deck.perm_k(k=4):
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

secl = second_trick_leader_value(short_deck, secfd)
secld = second_trick_leader_decision(short_deck, secl)
# uninit:
secld = second_trick_leader_decision(short_deck)

def first_trick_follower_value(deck:Urn, secld=None, secfd=None):
    """
    computes a dict which is keyed by [(unplayed1, unplayed2, myplayed1, theirplayed1)] with value
    the conditional expected match value from 'my' POV of following in the first trick with myplayed1.
    the expected value is _conditional_ on those cards having been played, and everyone playing the optimal
    decisions.
    By assumption unplayed1 >= unplayed2
    """
    if secld is None:
        secld = second_trick_leader_decision(deck)
    if secfd is None:
        secfd = second_trick_follower_decision(deck)
    firf = {}
    for myun1, myun2, mypl1, thpl1, ignore_wt, tail_urn in deck.perm_k(k=4):
        if myun1 < myun2:
            continue
        first_trick = _score_trick(mypl1, thpl1)
        numr = 0
        deno = 0
        for thun1, thun2, wt, _ in tail_urn.perm_k(k=2):
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

firf = first_trick_follower_value(short_deck, secld, secfd)

def first_trick_follower_decision(deck: Urn, firf=None):
    """
    computes a dict which is keyed by [(unplayed1, unplayed2, unplayed3, theirplayed1)] with value
    the conditional expected match value from 'my' POV of following in the first trick, and the optimal card to play.
    the expected value is _conditional_ on those cards having been played, and everyone playing the optimal
    decisions.
    By assumption unplayed1 >= unplayed2 and unplayed2 >= unplayed3
    """
    if firf is None:
        firf = first_trick_follower_value(deck)
    firfd = {}
    for myun1, myun2, myun3, thpl1, _, _ in deck.perm_k(k=4):
        if (myun1 < myun2) or (myun2 < myun3):
            continue
        # value from playing 1, 2 or 3
        val1 = firf[(myun2, myun3, myun1, thpl1)]
        val2 = firf[(myun1, myun3, myun2, thpl1)]
        val3 = firf[(myun1, myun2, myun3, thpl1)]
        firfd[(myun1, myun2, myun3, thpl1)] = max([(val1, myun1), (val2, myun2), (val3, myun3)])
    return firfd

firfd = first_trick_follower_decision(short_deck, firf)

# now the first trick leader value.
def first_trick_leader_value(deck: Urn, firfd=None, secld=None, secfd=None):
    """
    computes a dict which is keyed by [(unplayed1, unplayed2, myplayed1)] with value
    the conditional expected match value from 'my' POV of following in the first trick with myplayed1.
    the expected value is _conditional_ on those cards having been played, and everyone playing the optimal
    decisions.
    By assumption unplayed1 >= unplayed2
    """
    if secld is None:
        secld = second_trick_leader_decision(deck)
    if secfd is None:
        secfd = second_trick_follower_decision(deck)
    if firfd is None:
        firf = first_trick_follower_value(deck, secld, secfd)
        firfd = first_trick_follower_decision(deck, firf)
    firl = {}
    for myun1, myun2, mypl1, ignore_wt, tail_urn in deck.perm_k(k=3):
        if myun1 < myun2:
            continue
        numr = 0
        deno = 0
        for thun1, thun2, thun3, wt,_ in tail_urn.perm_k(k=3):
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

firl = first_trick_leader_value(short_deck)

# now the first trick leader decision.
def first_trick_leader_decision(deck: Urn, firl=None):
    """
    computes a dict which is keyed by [(unplayed1, unplayed2, unplayed3)] with value
    the conditional expected match value from 'my' POV of following in the first trick with myplayed1, and the optimal move.
    the expected value is _conditional_ on those cards having been played, and everyone playing the optimal
    decisions.
    By assumption unplayed1 >= unplayed2 >= unplayed3
    """
    if firl is None:
        firl = first_trick_leader_value(deck)
    firld = {}
    for myun1, myun2, myun3, _, _ in deck.perm_k(k=3):
        if (myun1 < myun2) or (myun2 < myun3):
            continue
        # value from playing 1, 2 or 3
        val1 = firl[(myun2, myun3, myun1)]
        val2 = firl[(myun1, myun3, myun2)]
        val3 = firl[(myun1, myun2, myun3)]
        firld[(myun1, myun2, myun3)] = max([(val1, myun1), (val2, myun2), (val3, myun3)])
    return firld

firl = first_trick_leader_value(short_deck, firfd, secld, secfd)

# now the first trick leader value.
firld = first_trick_leader_decision(short_deck, firl)

#for vim modeline: (do not edit)
# vim:ts=4:sw=4:sts=4:tw=79:sta:et:ai:nu:fdm=indent:syn=python:ft=python:tag=.py_tags;:cin:fo=croql
