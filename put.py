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

from copy import copy
from functools import cached_property
# this is in 3.9, I'm afraid:
# from functools import cache
from functools import lru_cache
cache = lru_cache(maxsize=None)

from urn import Urn
from collections import Counter

from enum import Enum, IntEnum, auto
from functools import total_ordering
import csv
import rootfind

def root_polish(f, x0, y0=None, ytol=1e-15, **kwargs):
    """
    seeks to find a solution to
    f(x) = 1 - x
    where 0 < f(x) < 1 for x in [0, 1]
    and f(x) is an increasing function.
    Does the following:
    1 if abs(f(x0) + x0 - 1) < ytol, just return x0
    2 otherwise call the illinois method.
    """
    iter = 0
    if y0 is None:
        y0 = f(x0)
        iter += 1
        if verbosity > 0:
            print(f"{iter}: {x0}, {y0 + x0 - 1}")
    if abs(y0 + x0 - 1) < ytol:
        return x0
    else:
        gx = lambda x: f(x) + x - 1
        if y0 < 1 - x0:
            a, fa, b, fb = (x0, y0 + x0 - 1, 1, None)
        else:
            a, fa, b, fb = (0, None, x0, y0 + x0 - 1)
        return rootfind.illinois_method(f=gx, a=a, b=b, fa=fa, fb=fb, ytol=ytol, **kwargs)



"""
master_deck = Urn(Counter({k:4 for k in range(13)}) + Counter({13:2}))
short_deck = Urn(Counter({k:4 for k in range(5)}))
# 2 jokers as "50", 12 3,2,Ace, 12 face cards ("10"), 12 789, and 12 456.
weird_deck = Urn(Counter({50:2, 32:12, 10:12, 7: 12, 4:12}))
"""


class PutRules():
    def __init__(self, deck, joker_func):
        self.__deck = deck
        self.__joker_func = joker_func
    @property
    def deck(self):
        return copy(self.__deck)
    @staticmethod
    def score_trick(play1, play2):
        """
        +/-1 or 0 from player 1's perspective.
        """
        return 1 if play1 > play2 else (-1 if play1 < play2 else 0)
    @staticmethod
    def score_match(trick1, trick2, trick3, joker_1=False, joker_2=False):
        """
        the trick scores are from player 1's perspective.
        +1 if player 1 wins,
         0 if a tie
        -1 if player 2 wins.
        aggregate them to a match win/loss from player 1's perspective.

        Also accepts Booleans for whether player 1 or player 2 played Joker cards, or both.
        In the case of a joker played, the side that played a joker will only win on
        2 wins and a tie or 2 wins and a loss.
        """
        stricks = sorted([trick1, trick2, trick3])
        if joker_1 and joker_2:
            # no possibility of a 3 win condition if both played jokers:
            # either they played simultaneously and so there is a tie,
            # or each player won 1 trick with their joker.
            if stricks[0] <= 0 and stricks[1] > 0:
                return 1
            elif stricks[1] < 0 and stricks[2] >= 0:
                return -1
            else:
                return 0
        elif joker_1:
            if stricks[0] > 0:
                # won all three and thus lost
                return -1
            elif stricks[0] <= 0 and stricks[1] > 0:
                return 1
            elif stricks[1] < 0:
                return -1
            else:
                return 0
        elif joker_2:
            if stricks[2] < 0:
                # won all three and thus lost
                return 1
            elif stricks[2] >= 0 and stricks[1] < 0:
                return -1
            elif stricks[1] > 0:
                return 1
            else:
                return 0
        else:
            if stricks[1] > 0:
                return 1
            elif stricks[1] < 0:
                return -1
            else:
                return 0
    def score_from(self, pair1, pair2, pair3):
        """
        determine if jokers were played, score each trick and return the match score
        """
        joker_1 = self.__joker_func(pair1[0]) or self.__joker_func(pair2[0]) or self.__joker_func(pair3[0])
        joker_2 = self.__joker_func(pair1[1]) or self.__joker_func(pair2[1]) or self.__joker_func(pair3[1])
        trick1 = self.score_trick(pair1[0], pair1[1])
        trick2 = self.score_trick(pair2[0], pair2[1])
        trick3 = self.score_trick(pair3[0], pair3[1])
        return self.score_match(trick1, trick2, trick3, joker_1=joker_1, joker_2=joker_2)

short_deck = Urn(Counter({k:4 for k in range(5)}))
pr = PutRules(deck=short_deck, joker_func=lambda x:x==4)
pr.score_from((2, 0), (1, 0), (0, 0))

class PutOptimalStrategy():
    """
    Consider a single deal of three cards each from a given deck.
    We find the optimal strategy of a risk neutral player for given conditional probabilities of winning the match
    conditional on winning this deal.
    That is, players try to maximize the probability of winning the match, which is to win five deals (or one at put).
    Consider the conditional probability of winning the match if we win, lose or tie this deal, call them
    pc_win, pc_lose, and pc_tie.
    Players seek to maximize pwin * pc_win + ptie * pc_tie + plose * pc_lose.
    Note that if the current tally is 4-4, (and thus there is no sense in calling 'put'),
    then pc_win = 1, pc_lose = 0, and pc_tie = 0.5 ???.
    (We probably have to recursively estimate pc_tie.)
    At each step the objective function we will compute (and then chose to maximize) is
      O = pwin * prob_win_con_win + (1-pwin-plose) * prob_win_con_tie + plose * prob_win_con_lose
        = pwin * (prob_win_con_win - prob_win_con_tie) + prob_win_con_tie + plose * (prob_win_con_lose - prob_win_con_tie)
    So it suffices to instead maximize 
      O - prob_win_con_tie = pwin * wt_win + plose * wt_lose
    where
      wt_win = prob_win_con_win - prob_win_con_tie
      wt_lose = prob_win_con_lose - prob_win_con_tie

    Valuation is optimal from the perspective of the player playing the trick, leader or follower.
    We will use 'Me' or 'My' to refer to the player leading the first trick, and 'They/Their' to 
    refer to the player following in the first trick.
    Valuations are generally from the perspective of who is playing that move.
    We assume that the first trick leader alternates in each deal. 

    Params for methods.

    pw_tup: a 3-tuple consisting of 
      prob_win_con_win:  the probability that "Me" wins the match given that "Me" wins this deal.
      prob_win_con_lose:  the probability that "Me" wins the match given that "Me" loses this deal.
      prob_win_con_tie:  the probability that "Me" wins the match given that "Me" and "They" tie this deal.

    The methods *_value return a dict mapping the observed data to a tuple of
    (match_win_prop, deal_win_prob, deal_lose_prob)
    and are contingent on making a given move.
    The methods *_decision return a dict mapping the observed data to a tuple of
    (optimal_move, optimal_match_win_prop, optimal_deal_win_prob, optimal_deal_lose_prob)


    """
    def __init__(self, rules):
        self.__rules = rules
    @staticmethod
    def _put_best(alist):
        """
        Given a list consisting of tuples of the form (card, valuation1, valuation2, ...),
        returns the 'maximal' tuple of the list, where the sort is in 
        ascending order of valuation1, but descending card value.
        """
        # we cannot negate cards but we can negate values
        return min(alist, key=lambda x: (-x[1], x[0]))
    @staticmethod
    def _get_wts(pw_tup):
        prob_win_con_win, prob_win_con_tie, prob_win_con_lose = pw_tup
        wt_win = prob_win_con_win - prob_win_con_tie
        wt_lose = prob_win_con_lose - prob_win_con_tie
        return (wt_win, wt_lose, prob_win_con_tie)
    @staticmethod
    def _opponent_tup(pw_tup):
        prob_win_con_win, prob_win_con_tie, prob_win_con_lose = pw_tup
        return (1-prob_win_con_lose, 1-prob_win_con_tie, 1-prob_win_con_win)
    @staticmethod
    def _put_tup(pw_tup):
        """
        when you call tup, it accelerates the win/lose probabilities. 
        perform that computation here.
        """
        _,  prob_win_con_tie, _ = pw_tup
        return (1, prob_win_con_tie, 0)
    @staticmethod
    def can_call_put(pw_tup):
        prob_win_con_win, _, prob_win_con_lose = pw_tup
        return prob_win_con_win < 1
    @cache
    def second_trick_follower_value(self, pw_tup):
        """
        computes a dict which is keyed by [(unplayed1, myplayed1, myplayed2, theirplayed1, theirplayed2)] with value
        the conditional expected match value from 'my' POV.
        the expected value is _conditional_ on those cards having been played.

        we add in the prob_win_con_tie so that these are probabilities of ultimately prevailing, and should be between 0 and 1.
        """
        secf = {}
        deck = self.__rules.deck
        wt_win, wt_lose, prob_win_con_tie = self._get_wts(pw_tup)
        for myun1, mypl1, mypl2, thpl1, thpl2, ignore_wt, tail_urn in deck.perm_k(k=5):
            numr_win = 0
            numr_los = 0
            deno = 0
            for thun1, wt, _ in tail_urn.perm_k(k=1):
                outcome = self.__rules.score_from((mypl1, thpl1), (mypl2, thpl2), (myun1, thun1))
                numr_win += wt * max(outcome, 0)
                numr_los -= wt * min(outcome, 0)
                deno += wt
            pr_win = numr_win / deno
            pr_los = numr_los / deno
            secf[(myun1, mypl1, mypl2, thpl1, thpl2)] = (prob_win_con_tie + (wt_win * pr_win + wt_lose * pr_los), pr_win, pr_los)
        return secf
    @cache
    def second_trick_follower_decision(self, pw_tup):
        """
        computes a dict which is keyed by [(unplayed1, unplayed2, myplayed1, theirplayed1, theirplayed2)] with value
        the optimal conditional expected match value from 'my' POV, and the card to play from my two unplayed cards.
        by convention unplayed1 >= unplayed2
        the expected value is _conditional_ on those cards having been played.
        """
        secf = self.second_trick_follower_value(pw_tup=pw_tup)
        secfd = {}
        deck = self.__rules.deck
        for myun1, myun2, mypl1, thpl1, thpl2, ignore_wt, tail_urn in deck.perm_k(k=5):
            if myun1 < myun2:
                continue
            val1 = secf.get((myun2, mypl1, myun1, thpl1, thpl2), None)
            if val1 is None:
                continue
            val2 = secf.get((myun1, mypl1, myun2, thpl1, thpl2))
            secfd[(myun1, myun2, mypl1, thpl1, thpl2)] = self._put_best([(myun1, *val1), (myun2, *val2)])
        return secfd
    @cache
    def second_trick_leader_value(self, pw_tup):
        """
        computes a dict which is keyed by [(unplayed1, myplayed1, myplayed2, theirplayed1)] with value
        the conditional expected match value from 'my' POV of leading with myplayed2 in the second
        trick. 
        the expected value is _conditional_ on those cards having been played, and on the opponent
        playing the optimal follow decision.
        By assumption since I am leading in the second trick, myplayed1 >= theirplayed1.
        """
        secfd = self.second_trick_follower_decision(pw_tup=self._opponent_tup(pw_tup))
        wt_win, wt_lose, prob_win_con_tie = self._get_wts(pw_tup)
        secl = {}
        deck = self.__rules.deck
        for myun1, mypl1, mypl2, thpl1, ignore_wt, tail_urn in deck.perm_k(k=4):
            if mypl1 < thpl1:
                continue
            numr_win = 0
            numr_los = 0
            deno = 0
            for thun1, thun2, wt, _ in tail_urn.perm_k(k=2):
                if wt <= 0:
                    continue
                # figure out what they follow with:
                thpl2, _, _, _ = secfd[(max(thun1, thun2), min(thun1, thun2), thpl1, mypl1, mypl2)]
                thpl3 = thun2 if thpl2==thun1 else thun1
                outcome = self.__rules.score_from((mypl1, thpl1), (mypl2, thpl2), (myun1, thpl3))
                numr_win += wt * max(outcome, 0)
                numr_los -= wt * min(outcome, 0)
                deno += wt
            pr_win = numr_win / deno
            pr_los = numr_los / deno
            secl[(myun1, mypl1, mypl2, thpl1)] = (prob_win_con_tie + (wt_win * pr_win + wt_lose * pr_los), pr_win, pr_los)
        return secl
    @cache
    def second_trick_leader_decision(self, pw_tup):
        """
        computes a dict which is keyed by [(unplayed1, unplayed2, myplayed1, theirplayed1)] with value
        the conditional expected match value from 'my' POV, and the optimal card to lead with in the second trick.
        the expected value is _conditional_ on those cards having been played, and on the opponent
        playing the optimal follow decision.
        By assumption since I am leading in the second trick, myplayed1 >= theirplayed1.
        We also assume unplayed1 >= unplayed2
        """
        secl = self.second_trick_leader_value(pw_tup=pw_tup)
        secld = {}
        deck = self.__rules.deck
        for myun1, myun2, mypl1, thpl1, _, _ in deck.perm_k(k=4):
            if myun1 < myun2:
                continue
            if mypl1 < thpl1:
                continue
            val1 = secl.get((myun2, mypl1, myun1, thpl1), None)
            if val1 is None:
                continue
            val2 = secl.get((myun1, mypl1, myun2, thpl1))
            secld[(myun1, myun2, mypl1, thpl1)] = self._put_best([(myun1, *val1), (myun2, *val2)])
        return secld
    @cache
    def first_trick_follower_value(self, pw_tup):
        """
        computes a dict which is keyed by [(unplayed1, unplayed2, myplayed1, theirplayed1)] with value
        the conditional expected match value from 'my' POV of following in the first trick with myplayed1.
        the expected value is _conditional_ on those cards having been played, and everyone playing the optimal
        decisions.
        By assumption unplayed1 >= unplayed2
        """
        secld = self.second_trick_leader_decision(pw_tup=pw_tup)
        secfd = self.second_trick_follower_decision(pw_tup=pw_tup)
        # from your opponent's POV:
        alt_secld = self.second_trick_leader_decision(pw_tup=self._opponent_tup(pw_tup))
        alt_secfd = self.second_trick_follower_decision(pw_tup=self._opponent_tup(pw_tup))
        wt_win, wt_lose, prob_win_con_tie = self._get_wts(pw_tup)
        firf = {}
        deck = self.__rules.deck
        for myun1, myun2, mypl1, thpl1, ignore_wt, tail_urn in deck.perm_k(k=4):
            if myun1 < myun2:
                continue
            numr_win = 0
            numr_los = 0
            deno = 0
            first_trick = self.__rules.score_trick(mypl1, thpl1)
            for thun1, thun2, wt, _ in tail_urn.perm_k(k=2):
                if wt <= 0:
                    continue
                if first_trick > 0:
                    # we lead in the second trick
                    # what should we lead with?
                    mypl2, _, _, _ = secld[(max(myun1, myun2), min(myun1, myun2), mypl1, thpl1)]
                    # what should they follow in the second trick with?
                    thpl2, _, _, _ = alt_secfd[(max(thun1, thun2), min(thun1, thun2), thpl1, mypl1, mypl2)]
                else:
                    # first trick we tied or lost after following, so we follow
                    # in the second.
                    # figure out what they would lead with
                    thpl2, _, _, _ = alt_secld[(max(thun1, thun2), min(thun1, thun2), thpl1, mypl1)]
                    # what should we follow with in the second trick?
                    mypl2, _, _, _ = secfd[(max(myun1, myun2), min(myun1, myun2), mypl1, thpl1, thpl2)]
                mypl3 = myun1 if mypl2 == myun2 else myun2
                thpl3 = thun1 if thpl2 == thun2 else thun2
                outcome = self.__rules.score_from((mypl1, thpl1), (mypl2, thpl2), (mypl3, thpl3))
                numr_win += wt * max(outcome, 0)
                numr_los -= wt * min(outcome, 0)
                deno += wt
            pr_win = numr_win / deno
            pr_los = numr_los / deno
            firf[(myun1, myun2, mypl1, thpl1)] = (prob_win_con_tie + (wt_win * pr_win + wt_lose * pr_los), pr_win, pr_los)
        return firf
    @cache
    def first_trick_follower_decision(self, pw_tup):
        """
        computes a dict which is keyed by [(unplayed1, unplayed2, unplayed3, theirplayed1)] with value
        the conditional expected match value from 'my' POV of following in the first trick, and the optimal card to play.
        the expected value is _conditional_ on those cards having been played, and everyone playing the optimal
        decisions.
        By assumption unplayed1 >= unplayed2 and unplayed2 >= unplayed3
        """
        firf = self.first_trick_follower_value(pw_tup=pw_tup)
        firfd = {}
        deck = self.__rules.deck
        for myun1, myun2, myun3, thpl1, _, _ in deck.perm_k(k=4):
            if (myun1 < myun2) or (myun2 < myun3):
                continue
            # value from playing 1, 2 or 3
            val1 = firf[(myun2, myun3, myun1, thpl1)]
            val2 = firf[(myun1, myun3, myun2, thpl1)]
            val3 = firf[(myun1, myun2, myun3, thpl1)]
            firfd[(myun1, myun2, myun3, thpl1)] = self._put_best([(myun1, *val1), (myun2, *val2), (myun3, *val3)])
        return firfd
    @cache
    def first_trick_leader_value(self, pw_tup):
        """
        computes a dict which is keyed by [(unplayed1, unplayed2, myplayed1)] with value
        the conditional expected match value from 'my' POV of leading in the first trick with myplayed1.
        the expected value is _conditional_ on those cards having been played, and everyone playing the optimal
        decisions.
        By assumption unplayed1 >= unplayed2 and unplayed2 >= unplayed3

        2FIX: have to modify this to also return the probability of winning or losing _this deal_.
        Probably have to do that for _all_ the functions, sadly.
        """
        secld = self.second_trick_leader_decision(pw_tup=pw_tup)
        secfd = self.second_trick_follower_decision(pw_tup=pw_tup)
        # from your opponent's POV:
        alt_secld = self.second_trick_leader_decision(pw_tup=self._opponent_tup(pw_tup))
        alt_secfd = self.second_trick_follower_decision(pw_tup=self._opponent_tup(pw_tup))
        # first round stuff; this is from your opponent's POV
        firfd = self.first_trick_follower_decision(pw_tup=self._opponent_tup(pw_tup))
        wt_win, wt_lose, prob_win_con_tie = self._get_wts(pw_tup)
        firl = {}
        deck = self.__rules.deck
        for myun1, myun2, mypl1, ignore_wt, tail_urn in deck.perm_k(k=3):
            if myun1 < myun2:
                continue
            numr_win = 0
            numr_los = 0
            deno = 0
            for thun1, thun2, thun3, wt,_ in tail_urn.perm_k(k=3):
                if wt <= 0:
                    continue
                sord = sorted([thun1, thun2, thun3], reverse=True)
                thpl1, _, _, _ = firfd[(*sord, mypl1)]
                # get their unplayed cards.
                if thpl1 == thun1:
                    threm1, threm2 = (max(thun2, thun3), min(thun2, thun3))
                elif thpl1 == thun2:
                    threm1, threm2 = (max(thun1, thun3), min(thun1, thun3))
                else:
                    threm1, threm2 = (max(thun1, thun2), min(thun1, thun2))
                first_trick = self.__rules.score_trick(mypl1, thpl1)
                # depending on who wins first trick we have different leader/follower in second.
                # actually this needs to be modified depending on who leads the
                # trick, because they will have different wt_win and whatnot.
                # sigh.
                if first_trick >= 0:
                    # win or tie, I lead again
                    mypl2, _, _, _ = secld[(myun1, myun2, mypl1, thpl1)]
                    # their response is:
                    thpl2, _, _, _ = alt_secfd[(threm1, threm2, thpl1, mypl1, mypl2)]
                else:
                    # they lead.
                    thpl2, _, _, _ = alt_secld[(threm1, threm2, thpl1, mypl1)]
                    # my response should be
                    mypl2, _, _, _ = secfd[(myun1, myun2, mypl1, thpl1, thpl2)]
                    pass
                mypl3 = myun1 if mypl2 == myun2 else myun2
                thpl3 = threm1 if thpl2 == threm2 else threm2
                outcome = self.__rules.score_from((mypl1, thpl1), (mypl2, thpl2), (mypl3, thpl3))
                numr_win += wt * max(outcome, 0)
                numr_los -= wt * min(outcome, 0)
                deno += wt
            pr_win = numr_win / deno
            pr_los = numr_los / deno
            firl[(myun1, myun2, mypl1)] = (prob_win_con_tie + (wt_win * pr_win + wt_lose * pr_los), pr_win, pr_los)
        return firl
    @cache
    def first_trick_leader_decision(self, pw_tup):
        """
        computes a dict which is keyed by [(unplayed1, unplayed2, unplayed3)] with value
        the conditional expected match value from 'my' POV of following in the first trick with myplayed1, and the optimal move.
        the expected value is _conditional_ on those cards having been played, and everyone playing the optimal
        decisions.
        By assumption unplayed1 >= unplayed2 >= unplayed3
        """
        firl = self.first_trick_leader_value(pw_tup=pw_tup)
        firld = {}
        deck = self.__rules.deck
        for myun1, myun2, myun3, _, _ in deck.perm_k(k=3):
            if (myun1 < myun2) or (myun2 < myun3):
                continue
            # value from playing 1, 2 or 3
            val1 = firl[(myun2, myun3, myun1)]
            val2 = firl[(myun1, myun3, myun2)]
            val3 = firl[(myun1, myun2, myun3)]
            firld[(myun1, myun2, myun3)] = self._put_best([(myun1, *val1), (myun2, *val2), (myun3, *val3)])
        return firld
    @cache
    def first_trick_call_put_decision(self, pw_tup):
        """
        computes a dict which is keyed by [(unplayed1, unplayed2, myplayed1)] with value
        the conditional expected match value from 'my' POV of calling put in the first trick.
        Calling put accelerates the probability of winning or losing based on this deal.
        By assumption unplayed1 >= unplayed2 >= unplayed3
        """
        firld = self.first_trick_leader_decision(self, pw_tup=pw_tup)
        ftpd = {}
        if self.can_call_put(pw_tup):
            put_firld = self.first_trick_leader_decision(self, pw_tup=self._put_tup(pw_tup))
            for key, npval in firld.items():
                _, noval, _, _ = npval
                _, yesval, _, _ = put_firld[key]
                ftpd[key] = ("call_put" if yesval > noval else "knock", max(noval, yesval))
        else:
            for key, npval in firld.items():
                noval, _ = npval
                ftpd[key] = ("knock", noval)
        return ftpd
    def first_trick_put_decision(self, pw_tup):
        """
        computes a dict which is keyed by [(unplayed1, unplayed2, myplayed1)] with value
        the conditional expected match value from 'my' POV of calling put in the first trick.
        Calling put accelerates the probability of winning or losing based on this deal.
        By assumption unplayed1 >= unplayed2 >= unplayed3
        """
        # do not know how to do this yet.
        pass
    @cache
    def first_trick_follower_unconditional_value(self, pw_tup):
        """
        computes a dict which is keyed by [(unplayed1, unplayed2, unplayed3)] with value
        the conditional expected match value from the first trick follower's POV.
        this is unconditional on move played. it is assumed that the first player plays their optimal card.
        By assumption unplayed1 >= unplayed2 >= unplayed3
        """
        firld = self.first_trick_leader_decision(pw_tup=self._opponent_tup(pw_tup))
        firfd = self.first_trick_follower_decision(pw_tup=pw_tup)
        deck = self.__rules.deck
        firfuv = {}
        # 2FIX: this should return pwin and plose of this deal ...
        for myun1, myun2, myun3, ignore_wt, tail_urn in deck.perm_k(k=3):
            if (myun1 < myun2) or (myun2 < myun3):
                continue
            numr_win = 0
            deno = 0
            for thun1, thun2, thun3, wt, _ in tail_urn.perm_k(k=3):
                sord = tuple(sorted([thun1, thun2, thun3], reverse=True))
                thpl1, _, _, _ = firld[sord]
                _, this_pwin, _, _ = firfd[(myun1, myun2, myun3, thpl1)]
                deno += wt
                numr_win += wt * this_pwin
            # need to add the pcon_win_con_tie part here...
            firfuv[(myun1, myun2, myun3)] = numr_win / deno
        return firfuv
    def _save_something(self, outfile, header_row, save_dict):
        """
        canonical way to sink to csv.
        """
        with open(outfile,'w') as out:
            csv_out=csv.writer(out)
            csv_out.writerow(header_row)
            for cads, out in save_dict.items():
                if isinstance(out, tuple):
                    arow = [*cads, *out]
                else:
                    arow = [*cads, out]
                csv_out.writerow(arow)
    def save_first_trick_leader_decision(self, outfile, pw_tup):
        """
        canonical way to sink to csv.
        """
        firld = self.first_trick_leader_decision(pw_tup=pw_tup)
        self._save_something(outfile=outfile, header_row=['card1','card2','card3','to_play','pwin_match','pwin_deal','plose_deal'], save_dict=firld)

    def save_first_trick_follower_unconditional_value(self, outfile, pw_tup, flip_sense:bool = True):
        """
        canonical way to sink to csv.

        Args:

          flip_sense: if true, we assume pw_tup is from the first trick leader's perspective,
                    and we flip its sense for you.
        """
        if flip_sense:
            pw_tup = self._opponent_tup(pw_tup)
        firfuv = self.first_trick_follower_unconditional_value(pw_tup=pw_tup)
        self._save_something(outfile=outfile, header_row=['card1','card2','card3','pwin'], save_dict=firfuv)

    def save_first_trick_follower_decision(self, outfile, pw_tup, flip_sense:bool = True):
        """
        canonical way to sink to csv.

        Args:

          flip_sense: if true, we assume pw_tup is from the first trick leader's perspective,
                    and we flip its sense for you.
        """
        if flip_sense:
            pw_tup = self._opponent_tup(pw_tup)
        firfd = self.first_trick_follower_decision(pw_tup=pw_tup)
        self._save_something(outfile=outfile, header_row=['card1','card2','card3','opponent_card','to_play','pwin_match','pwin_deal','plose_deal'], save_dict=firfd)

    def save_second_trick_leader_decision(self, outfile, pw_tup, flip_sense:bool = False):
        """
        canonical way to sink to csv.

        Args:

          flip_sense: if true, we assume pw_tup is from the first trick leader's perspective,
                    and we flip its sense for you.
        """
        if flip_sense:
            pw_tup = self._opponent_tup(pw_tup)
        secld = self.second_trick_leader_decision(pw_tup)
        self._save_something(outfile=outfile, header_row=['card1','card2','myplayed1','theirplayed1','to_play','pwin_match','pwin_deal','plose_deal'], save_dict=secld)

    def save_second_trick_follower_decision(self, outfile, pw_tup, flip_sense:bool = True):
        """
        canonical way to sink to csv.

        Args:

          flip_sense: if true, we assume pw_tup is from the first trick follower's perspective,
                    and we flip its sense for you.
        """
        if flip_sense:
            pw_tup = self._opponent_tup(pw_tup)
        secfd = self.second_trick_follower_decision(pw_tup)
        self._save_something(outfile=outfile, header_row=['card1','card2','myplayed1','theirplayed1','theirplayed2','to_play','pwin_match','pwin_deal','plose_deal'], save_dict=secfd)

    @cache
    def prob_win(self, pw_tup):
        """
        computes the probability that I will win the match, unconditional of the cards dealt, given that I lead this trick,
        and we have the given conditional probabilities of winning given the outcome of this deal.
        """
        firld = self.first_trick_leader_decision(pw_tup)
        numr_win = 0
        deno = 0
        deck = self.__rules.deck
        for myun1, myun2, myun3, wt, _ in deck.perm_k(k=3):
            mykey = tuple(sorted([myun1, myun2, myun3], reverse=True))
            deno += wt
            numr_win += wt * firld[mykey][1]
        return numr_win / deno
    def iterate_tie_pwin(self, pw_start, max_iter=50, min_diff=1e-7, verbosity=0):
        """
        iteratively update the middle value of pw_tup
        """
        ffunc = lambda x: self.prob_win(pw_tup=(pw_start[0], x, pw_start[2]))
        x1 = root_polish(ffunc, pw_start[1], ytol=min_diff, xtol=min_diff, max_iter=max_iter, verbosity=verbosity)
        return (pw_start[0], x1, pw_start[2])


"""
# careful looking at this, as it has _jokers_ in it.
short_deck = Urn(Counter({k:4 for k in range(5)}))
pr = PutRules(deck=short_deck, joker_func=lambda x:x==4)

# no joke deck
dum_deck = Urn(Counter({k:4 for k in range(7)}))
pr = PutRules(deck=dum_deck, joker_func=lambda x:False)

# bigger deck, with a joker
dum_deck = Urn(Counter({k:4 for k in range(10)}))
pr = PutRules(deck=dum_deck, joker_func=lambda x:False)
"""

"""
from urn import Urn
from put import *
#big_deck = Urn(Counter({k:4 for k in range(13)}))
#pr = PutRules(deck=big_deck, joker_func=lambda x:False)

lil_deck = Urn(Counter({k:4 for k in range(6)}))
pr = PutRules(deck=lil_deck, joker_func=lambda x:False)

pi_prev = 0.75
pi_prev = 0.4561
pi_prev = 0.4561581300641355
pi_prev = 0.75
agoo = PutOptimalStrategy(pr)
pw_next = agoo.iterate_tie_pwin((1, 1-pi_prev, 0), verbosity=1, min_diff=1e-13)
print(f"pi_prev = {1 - pw_next[1]}")

agoo.save_first_trick_leader_decision("/tmp/putfoo_000.csv", pw_next)
agoo.save_first_trick_follower_unconditional_value("/tmp/putfoo_001.csv", pw_next)
agoo.save_first_trick_follower_decision("/tmp/putfoo_002.csv", pw_next)
agoo.save_second_trick_leader_decision("/tmp/putfoo_003.csv", pw_next)
agoo.save_second_trick_follower_decision("/tmp/putfoo_004.csv", pw_next)

# try a bigger deck.
mid_deck = Urn(Counter({k:4 for k in range(10)}))
pr = PutRules(deck=mid_deck, joker_func=lambda x:False)

# for 10 card deck, no jokers
afoo = PutOptimalStrategy(pr)
pi_prev = 0.4532112055980586
pw_next = afoo.iterate_tie_pwin((1, 1-pi_prev, 0), verbosity=1, min_diff=1e-16)
print(f"pi_prev = {1 - pw_next[1]}")

afoo.save_first_trick_leader_decision("/tmp/putfoo_000.csv", pw_next)
afoo.save_first_trick_follower_unconditional_value("/tmp/putfoo_001.csv", pw_next)
afoo.save_first_trick_follower_decision("/tmp/putfoo_002.csv", pw_next)
afoo.save_second_trick_leader_decision("/tmp/putfoo_003.csv", pw_next)
afoo.save_second_trick_follower_decision("/tmp/putfoo_004.csv", pw_next)

# for 10 card deck plus 2 jokers
pi_prev = 0.47570996176217173

# try little deck plus 2 jokers
lil_deck = Urn(Counter({k:(4 if k < 6 else 2) for k in range(7)}))
pr = PutRules(deck=lil_deck, joker_func=lambda x:x==6)

pi_prev = 0.4656034904818125
abar = PutOptimalStrategy(pr)
pw_next = abar.iterate_tie_pwin((1, 1-pi_prev, 0), verbosity=1, min_diff=1e-16)
print(f"pi_prev = {1 - pw_next[1]}")

abar.save_first_trick_leader_decision("/tmp/putfoo_000.csv", pw_next)
abar.save_first_trick_follower_unconditional_value("/tmp/putfoo_001.csv", pw_next)
abar.save_first_trick_follower_decision("/tmp/putfoo_002.csv", pw_next)
abar.save_second_trick_leader_decision("/tmp/putfoo_003.csv", pw_next)
abar.save_second_trick_follower_decision("/tmp/putfoo_004.csv", pw_next)

#### 

# full size deck, no jokers
ful_deck = Urn(Counter({k:4 for k in range(13)}))
pr = PutRules(deck=ful_deck, joker_func=lambda x:False)

# for 13 card deck, no jokers
afoo = PutOptimalStrategy(pr)
pi_prev = 0.4522019143769842
pw_next = afoo.iterate_tie_pwin((1, 1-pi_prev, 0), verbosity=1, min_diff=1e-16)
print(f"pi_prev = {1 - pw_next[1]}")

afoo.save_first_trick_leader_decision("/tmp/put_fulldeck_000.csv", pw_next)
afoo.save_first_trick_follower_unconditional_value("/tmp/put_fulldeck_001.csv", pw_next)
afoo.save_first_trick_follower_decision("/tmp/put_fulldeck_002.csv", pw_next)
afoo.save_second_trick_leader_decision("/tmp/put_fulldeck_003.csv", pw_next)
afoo.save_second_trick_follower_decision("/tmp/put_fulldeck_004.csv", pw_next)

# full size deck, two jokers
fulj_deck = Urn(Counter({k:(4 if k < 13 else 2) for k in range(14)}))
pr = PutRules(deck=fulj_deck, joker_func=lambda x:False)

# for 13 card deck, with jokers?
afoo = PutOptimalStrategy(pr)
pi_prev = 0.45199056202682375
pw_next = afoo.iterate_tie_pwin((1, 1-pi_prev, 0), verbosity=1, min_diff=1e-16)
print(f"pi_prev = {1 - pw_next[1]}")

afoo.save_first_trick_leader_decision("/tmp/put_fulldeck_jk_000.csv", pw_next)
afoo.save_first_trick_follower_unconditional_value("/tmp/put_fulldeck_jk_001.csv", pw_next)
afoo.save_first_trick_follower_decision("/tmp/put_fulldeck_jk_002.csv", pw_next)
afoo.save_second_trick_leader_decision("/tmp/put_fulldeck_jk_003.csv", pw_next)
afoo.save_second_trick_follower_decision("/tmp/put_fulldeck_jk_004.csv", pw_next)

"""



# enum with ordering. See also Enum.OrderedEnum
# https://stackoverflow.com/a/39269589/164611
class PutCardOrder(Enum):
    Four = 0
    Five = 1
    Six = 2
    Seven = 3
    Eight = 4
    Nine = 5
    Ten = 6
    Jack = 7
    Queen = 8
    King = 9
    Ace = 10
    Two = 11
    Three = 12
    Joker = 13
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented
    
"""
put_deck = Urn(Counter({k:(4 if k != PutCardOrder.Joker else 2) for k in PutCardOrder}))
put_short_deck = Urn(Counter({k:(4 if k != PutCardOrder.Joker else 0) for k in PutCardOrder}))
pr = PutRules(deck=put_short_deck, joker_func=lambda x:x==PutCardOrder.Joker)
goo = PutOptimalStrategy(pr)
zedy = goo.first_trick_leader_decision

put_deck = Urn(Counter({k:(4 if k != PutCardOrder.Joker else 2) for k in PutCardOrder}))
put_deck.sample(5)
"""

from turn_based import StateMixin, HistoryMixin, AbstractSequentialGame, InvalidMoveException

def _opponent_of(player):
    return (player + 1) % 2

class PutGame(StateMixin, HistoryMixin, AbstractSequentialGame):
    def __init__(self, deck=None, turn=0, lead_rule='alternating'):
        """
        A game consists of multiple deals, each of which is three tricks.
        A deal can be a win, loss or tie for the first player. (or second; it is zero sum.)


        lead_rule: determines who leads the first trick in a deal. Can be strictly alternating,
                     winner leads or loser leads.
        """
        super().__init__(turn=turn)
        if deck is None:
            deck = Urn(Counter({k:(4 if k != PutCardOrder.Joker else 0) for k in PutCardOrder}))
        self.__deck = deck
        self.__winner = None
        self.__tally = [0, 0]
        self.__deal_wins = []
        self.__history = []
        assert lead_rule in ['alternating', 'winner_leads', 'loser_leads'], f"unknown {lead_rule}"
        self.lead_rule = lead_rule
        self._first_trick_leader = None
        # who leads the first trick in the first deal.
        # now deal
        self._new_deal()

    def _new_deal(self):
        if self._first_trick_leader is None:
            # no previous deals, set leader to whose turn it is.
            self._first_trick_leader = self.turn
        else:
            if self.lead_rule == 'alternating':
                self._first_trick_leader = _opponent_of(self._first_trick_leader)
            elif self.lead_rule == 'winner_leads':
                self._first_trick_leader = self.__deal_wins[-1]
            elif self.lead_rule == 'loser_leads':
                self._first_trick_leader = _opponent_of(self.__deal_wins[-1])
            self.__turn = self._first_trick_leader
        self.__put_state = 'none'
        deal = self.__deck.sample(6)
        self.__hands = [deal[:3], deal[3:]]
        is_joker = [x == PutCardOrder.Joker for x in deal]
        self.__had_joker = (any(is_joker[:3]), any(is_joker[3:]))
        self.__trick = 0
        self.__trick_history = [None] * 3
        self.__tricks_won = [0, 0]
        self.__played_card = None

    def _check_win(self):
        if self.__tally[0] > 4:
            self.__winner = 0
        elif self.__tally[1] > 4:
            self.__winner = 1
        else:
            self.__winner = None

    @property
    def winner(self):
        return self.__winner

    @property
    def history(self):
        return self.__history

    @property
    def hands(self):
        return self.__hands

    @property
    def n_players(self):
        return 2

    @property
    def valid_moves(self):
        if self.winner is not None:
            return []
        else:
            retv = []
            if self.__put_state == 'called':
                return ['fold', 'see']
            elif self.__put_state == 'none' and self.__tally[self.turn] < 4:
                # cannot call put if you have tally 4.
                retv.append('call_put')
            retv.extend(self.__hands[self.turn])
            return retv
    def play(self, move):
        if move not in self.valid_moves:
            raise InvalidMoveException
        if self.winner is None:
            self.__history.append((self.turn, move))
            if self.__put_state == 'called':
                if move == 'see':
                    self.__put_state = 'accepted'
                    # may have to advance, depending on when put was called.
                    # this is awful; need something better to determine who
                    # plays first in a trick and who is second.
                    if self.__played_card is None:
                        self.__turn = 0
                    else:
                        self.__turn = 1
                elif move == 'fold':
                    # opponent wins a point
                    self.__tally[_opponent_of(self.turn)] += 1
                    self._check_win()
                    if self.winner is None:
                        self._new_deal()
                else:
                    raise NotImplementedError
            elif move == 'call_put':
                self.__put_state = 'called'
                self._advance() 
            else:
                cur_player = self.turn
                oth_player = _opponent_of(cur_player)
                self.__hands[cur_player].remove(move)
                if self.__played_card is None:
                    self.__played_card = move
                    self._advance()
                else:
                    # trick is complete
                    self.__trick_history[self.__trick] = { oth_player: self.__played_card, cur_player: move }
                    if move > self.__played_card:
                        self.__tricks_won[cur_player] += 1
                        # do not advance for the next trick leader
                    else:
                        if move < self.__played_card:
                            self.__tricks_won[oth_player] += 1
                        # change who leads the next trick
                        self._advance()
                    self.__trick += 1
                    self.__played_card = None
                    if self.__trick > 2:
                        # deal is done.
                        if (self.__tricks_won[0] >= 2 and not self.__had_joker[0]) or (self.__tricks_won[0] == 2 and self.__had_joker[0]):
                            deal_winner = 0
                        elif (self.__tricks_won[1] >= 2 and not self.__had_joker[1]) or (self.__tricks_won[1] == 2 and self.__had_joker[1]):
                            deal_winner = 1
                        self.__deal_wins.append(deal_winner)
                        self.__tally[deal_winner] += 1
                        self._check_win()
                        if self.winner is None:
                            self._new_deal()



"""
import put
from importlib import reload
reload(put)

dum = put.PutGame()
import random
# can play any multiplayer game.
from turn_based import AbstractSequentialGame
def random_player(gameboard: AbstractSequentialGame):
    return random.choices(gameboard.valid_moves, k=1)[0]

mov = random_player(dum)
dum.play(mov)
dum.valid_moves
mov = random_player(dum)
dum.play(mov)
dum.valid_moves
dum.play('see')


dum = put.PutGame()
dum.play(dum.valid_moves[1])
dum.play('call_put')
dum.valid_moves
dum.play('see')
dum.valid_moves
"""


#for vim modeline: (do not edit)
# vim:ts=4:sw=4:sts=4:tw=79:sta:et:ai:nu:fdm=indent:syn=python:ft=python:tag=.py_tags;:cin:fo=croql
