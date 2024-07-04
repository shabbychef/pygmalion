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

from urn import Urn
from collections import Counter

from enum import Enum, IntEnum, auto
from functools import total_ordering

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
    This is for a single deal of three tricks. 
    But we are always trying to maximize the probability of winning the match, which is to win five deals (or one at put).
    So this takes as input the conditional probability of winning the match if we win, lose or tie this deal.
    Those are pc_win, pc_lose, and pc_tie.
    Then we always seek to maximize pwin * pc_win + ptie * pc_tie + plose * pc_lose.
    Note that if the current tally is 4-4, which is what we assume here, because then there is no sense in calling 'put',
    then pc_win = 1, pc_lose = 0, and pc_tie = ??.
    We probably have to recursively estimate pc_tie.

    At each step the objective function we will compute (and then chose to maximize) is
    O = pwin * prob_win_con_win + ptie * prob_win_con_tie + (1 - pwin - ptie) * prob_win_con_lose
      = pwin * (prob_win_con_win - prob_win_con_lose) + ptie * (prob_win_con_tie - prob_win_con_lose) + prob_win_con_lose
    So it suffices to maximize instead O - prob_win_con_lose
    """
    def __init__(self, rules, prob_win_con_win=1, prob_win_con_lose=0, prob_win_con_tie=0.5):
        self.__rules = rules
        self.prob_win_con_win=prob_win_con_win
        self.prob_win_con_lose=prob_win_con_lose
        self.prob_win_con_tie=prob_win_con_tie
        self.wt_win = prob_win_con_win - prob_win_con_lose
        self.wt_tie = prob_win_con_tie - prob_win_con_lose
    @staticmethod
    def _put_best(alist):
        """
        Given a list consisting of tuples of the form (valuation, card),
        returns the 'maximal' tuple of the list, where the sort is in 
        ascending valuation, but descending card value.
        """
        # we cannot negate cards but we can negate values
        return min(alist, key=lambda x: (-x[0], x[1]))
    @cached_property
    def second_trick_follower_value(self):
        """
        computes a dict which is keyed by [(unplayed1, myplayed1, myplayed2, theirplayed1, theirplayed2)] with value
        the conditional expected match value from 'my' POV.
        the expected value is _conditional_ on those cards having been played.
        """
        secf = {}
        deck = self.__rules.deck
        for myun1, mypl1, mypl2, thpl1, thpl2, ignore_wt, tail_urn in deck.perm_k(k=5):
            numr_win = 0
            numr_tie = 0
            deno = 0
            for thun1, wt, _ in tail_urn.perm_k(k=1):
                outcome = self.__rules.score_from((mypl1, thpl1), (mypl2, thpl2), (myun1, thun1))
                numr_win += wt * max(outcome, 0)
                numr_tie += wt * (1 - abs(outcome))
                deno += wt
            secf[(myun1, mypl1, mypl2, thpl1, thpl2)] = (self.wt_win * numr_win + self.wt_tie * numr_tie) / deno
        return secf
    @cached_property
    def second_trick_follower_decision(self):
        """
        computes a dict which is keyed by [(unplayed1, unplayed2, myplayed1, theirplayed1, theirplayed2)] with value
        the optimal conditional expected match value from 'my' POV, and the card to play from my two unplayed cards.
        by convention unplayed1 >= unplayed2
        the expected value is _conditional_ on those cards having been played.
        """
        secf = self.second_trick_follower_value
        secfd = {}
        deck = self.__rules.deck
        for myun1, myun2, mypl1, thpl1, thpl2, ignore_wt, tail_urn in deck.perm_k(k=5):
            if myun1 < myun2:
                continue
            val1 = secf.get((myun2, mypl1, myun1, thpl1, thpl2), None)
            if val1 is None:
                continue
            val2 = secf.get((myun1, mypl1, myun2, thpl1, thpl2))
            secfd[(myun1, myun2, mypl1, thpl1, thpl2)] = self._put_best([(val1, myun1), (val2, myun2)])
        return secfd
    @cached_property
    def second_trick_leader_value(self):
        """
        computes a dict which is keyed by [(unplayed1, myplayed1, myplayed2, theirplayed1)] with value
        the conditional expected match value from 'my' POV of leading with myplayed2 in the second
        trick. 
        the expected value is _conditional_ on those cards having been played, and on the opponent
        playing the optimal follow decision.
        By assumption since I am leading in the second trick, myplayed1 >= theirplayed1.
        """
        secfd = self.second_trick_follower_decision
        secl = {}
        deck = self.__rules.deck
        for myun1, mypl1, mypl2, thpl1, ignore_wt, tail_urn in deck.perm_k(k=4):
            if mypl1 < thpl1:
                continue
            numr_win = 0
            numr_tie = 0
            deno = 0
            for thun1, thun2, wt, _ in tail_urn.perm_k(k=2):
                if wt <= 0:
                    continue
                # figure out what they follow with:
                _, thpl2 = secfd[(max(thun1, thun2), min(thun1, thun2), thpl1, mypl1, mypl2)]
                thpl3 = thun2 if thpl2==thun1 else thun1
                outcome = self.__rules.score_from((mypl1, thpl1), (mypl2, thpl2), (myun1, thpl3))
                numr_win += wt * max(outcome, 0)
                numr_tie += wt * (1 - abs(outcome))
                deno += wt
            secl[(myun1, mypl1, mypl2, thpl1)] = (self.wt_win * numr_win + self.wt_tie * numr_tie) / deno
        return secl
    @cached_property
    def second_trick_leader_decision(self):
        """
        computes a dict which is keyed by [(unplayed1, unplayed2, myplayed1, theirplayed1)] with value
        the conditional expected match value from 'my' POV, and the optimal card to lead with in the second trick.
        the expected value is _conditional_ on those cards having been played, and on the opponent
        playing the optimal follow decision.
        By assumption since I am leading in the second trick, myplayed1 >= theirplayed1.
        We also assume unplayed1 >= unplayed2
        """
        secl = self.second_trick_leader_value
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
            secld[(myun1, myun2, mypl1, thpl1)] = self._put_best([(val1, myun1), (val2, myun2)])
        return secld
    @cached_property
    def first_trick_follower_value(self):
        """
        computes a dict which is keyed by [(unplayed1, unplayed2, myplayed1, theirplayed1)] with value
        the conditional expected match value from 'my' POV of following in the first trick with myplayed1.
        the expected value is _conditional_ on those cards having been played, and everyone playing the optimal
        decisions.
        By assumption unplayed1 >= unplayed2
        """
        secld = self.second_trick_leader_decision
        secfd = self.second_trick_follower_decision
        firf = {}
        deck = self.__rules.deck
        for myun1, myun2, mypl1, thpl1, ignore_wt, tail_urn in deck.perm_k(k=4):
            if myun1 < myun2:
                continue
            numr_win = 0
            numr_tie = 0
            deno = 0
            first_trick = self.__rules.score_trick(mypl1, thpl1)
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
                outcome = self.__rules.score_from((mypl1, thpl1), (mypl2, thpl2), (mypl3, thpl3))
                numr_win += wt * max(outcome, 0)
                numr_tie += wt * (1 - abs(outcome))
                deno += wt
            firf[(myun1, myun2, mypl1, thpl1)] = (self.wt_win * numr_win + self.wt_tie * numr_tie) / deno
        return firf
    @cached_property
    def first_trick_follower_decision(self):
        """
        computes a dict which is keyed by [(unplayed1, unplayed2, unplayed3, theirplayed1)] with value
        the conditional expected match value from 'my' POV of following in the first trick, and the optimal card to play.
        the expected value is _conditional_ on those cards having been played, and everyone playing the optimal
        decisions.
        By assumption unplayed1 >= unplayed2 and unplayed2 >= unplayed3
        """
        firf = self.first_trick_follower_value
        firfd = {}
        deck = self.__rules.deck
        for myun1, myun2, myun3, thpl1, _, _ in deck.perm_k(k=4):
            if (myun1 < myun2) or (myun2 < myun3):
                continue
            # value from playing 1, 2 or 3
            val1 = firf[(myun2, myun3, myun1, thpl1)]
            val2 = firf[(myun1, myun3, myun2, thpl1)]
            val3 = firf[(myun1, myun2, myun3, thpl1)]
            firfd[(myun1, myun2, myun3, thpl1)] = self._put_best([(val1, myun1), (val2, myun2), (val3, myun3)])
        return firfd
    @cached_property
    def first_trick_leader_value(self):
        """
        computes a dict which is keyed by [(unplayed1, unplayed2, myplayed1)] with value
        the conditional expected match value from 'my' POV of following in the first trick with myplayed1.
        the expected value is _conditional_ on those cards having been played, and everyone playing the optimal
        decisions.
        By assumption unplayed1 >= unplayed2
        """
        secld = self.second_trick_leader_decision
        secfd = self.second_trick_follower_decision
        firf = self.first_trick_follower_value
        firfd = self.first_trick_follower_decision
        firl = {}
        deck = self.__rules.deck
        for myun1, myun2, mypl1, ignore_wt, tail_urn in deck.perm_k(k=3):
            if myun1 < myun2:
                continue
            numr_win = 0
            numr_tie = 0
            deno = 0
            for thun1, thun2, thun3, wt,_ in tail_urn.perm_k(k=3):
                if wt <= 0:
                    continue
                sord = sorted([thun1, thun2, thun3], reverse=True)
                _, thpl1 = firfd[(*sord, mypl1)]
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
                outcome = self.__rules.score_from((mypl1, thpl1), (mypl2, thpl2), (mypl3, thpl3))
                numr_win += wt * max(outcome, 0)
                numr_tie += wt * (1 - abs(outcome))
                deno += wt
            firl[(myun1, myun2, mypl1)] = (self.wt_win * numr_win + self.wt_tie * numr_tie) / deno
        return firl
    @cached_property
    def first_trick_leader_decision(self):
        """
        computes a dict which is keyed by [(unplayed1, unplayed2, unplayed3)] with value
        the conditional expected match value from 'my' POV of following in the first trick with myplayed1, and the optimal move.
        the expected value is _conditional_ on those cards having been played, and everyone playing the optimal
        decisions.
        By assumption unplayed1 >= unplayed2 >= unplayed3
        """
        firl = self.first_trick_leader_value
        firld = {}
        deck = self.__rules.deck
        for myun1, myun2, myun3, _, _ in deck.perm_k(k=3):
            if (myun1 < myun2) or (myun2 < myun3):
                continue
            # value from playing 1, 2 or 3
            val1 = firl[(myun2, myun3, myun1)]
            val2 = firl[(myun1, myun3, myun2)]
            val3 = firl[(myun1, myun2, myun3)]
            firld[(myun1, myun2, myun3)] = self._put_best([(val1, myun1), (val2, myun2), (val3, myun3)])
        return firld

short_deck = Urn(Counter({k:4 for k in range(5)}))
pr = PutRules(deck=short_deck, joker_func=lambda x:x==4)

goo = PutOptimalStrategy(pr)
# careful looking at this, as it has _jokers_ in it.
zedy = goo.first_trick_leader_decision

dum_deck = Urn(Counter({k:4 for k in range(7)}))
pr = PutRules(deck=dum_deck, joker_func=lambda x:False)
goo = PutOptimalStrategy(pr)
zedy = goo.first_trick_leader_decision


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
