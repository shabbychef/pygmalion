#! /usr/bin/env python
# coding: utf-8
#
"""
.. module pygmalion:: pygmalion
   :synopsis: representation of cards

.. moduleauthor: Steven E. Pav <steven@gilgamath.com>

    Created: 2024.05.02
    Copyright: Steven E. Pav, 2024
    Author: Steven E. Pav
    Comments: Steven E. Pav
"""

import random
from abc import ABC, abstractmethod
from random import shuffle


class AbstractCardDeck(ABC):
    @property
    @abstractmethod
    def len(self):
        """
        return the number of cards in the deck.
        """
        pass

    @abstractmethod
    def shuffle(self):
        """
        shuffles the deck in place
        """
        pass

    @abstractmethod
    def peek(self):
        """
        looks at the top card in the deck, returning its value
        """
        pass

    @abstractmethod
    def draw(self, with_replacement=False):
        """
        returns the value of the top card,
        optionally replacing it on the bottom of the deck.
        """
        pass

    @abstractmethod
    def merge(self, other):
        """
        add the other deck to the bottom of the self deck, modifying the self deck.
        """
        pass


class ListCardDeck(AbstractCardDeck):
    def __init__(self, cards):
        self.cards = cards

    @property
    def len(self):
        return len(self.cards)

    def shuffle(self):
        random.shuffle(self.cards)

    def peek(self):
        return self.cards[0]

    def draw(self, with_replacement=False):
        retv = self.cards.pop(0)
        if with_replacement:
            self.cards.append(retv)
        return retv

    def merge(self, other):
        self.cards.extend(other.cards)
        return self


import itertools

foo = ListCardDeck(
    list(itertools.product(["hearts", "spades", "diamonds", "clubs"], range(1, 14)))
)
foo.peek()
foo.shuffle()


class FrenchCardDeck(ListCardDeck):
    def __init__(self):
        cards = list(itertools.product(FrenchCardSuit, FrenchCardRank))
        super().__init__(cards)


foo = FrenchCardDeck()


from enum import Enum, IntEnum, auto


class FrenchCardSuit(IntEnum):
    """
    Actually a French card suit
    """

    Spades = auto()
    Hearts = auto()
    Diamonds = auto()
    Clubs = auto()


class FrenchCardRank(Enum):
    """
    Do not impose an order on the ranks, as it depends on games.
    """

    Ace = auto()
    Two = auto()
    Three = auto()
    Four = auto()
    Five = auto()
    Six = auto()
    Seven = auto()
    Eight = auto()
    Nine = auto()
    Ten = auto()
    Jack = auto()
    Queen = auto()
    King = auto()


FrenchCardRank.Ace < FrenchCardRank.King
dict(FrenchCardRank)

FrenchCardSuit.Spades

foo = itertools.product(
    FrenchCardSuit.__members__.items(), FrenchCardRank.__members__.items()
)


# this doesn't work exactly
Enum(
    "TestFrenchCard",
    list(
        itertools.product(
            FrenchCardSuit.__members__.items(), FrenchCardRank.__members__.items()
        )
    ),
)


class FrenchCard(Enum):
    """
    Do not impose an order on the ranks, as it depends on games.
    """

    Ace = auto()
    Two = auto()
    Three = auto()
    Four = auto()
    Five = auto()
    Six = auto()
    Seven = auto()
    Eight = auto()
    Nine = auto()
    Ten = auto()
    Jack = auto()
    Queen = auto()
    King = auto()


# for vim modeline: (do not edit)
# vim:ts=4:sw=4:sts=4:tw=79:sta:et:ai:nu:fdm=indent:syn=python:ft=python:tag=.py_tags;:cin:fo=croql
