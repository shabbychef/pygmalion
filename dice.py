#! /usr/bin/env python
# coding: utf-8
#
"""
.. module pygmalion:: pygmalion
   :synopsis: representation of dice and other finite discrete probability distributions.

.. moduleauthor: Steven E. Pav <steven@gilgamath.com>

    Created: 2024.05.03
    Copyright: Steven E. Pav, 2024
    Author: Steven E. Pav
    Comments: Steven E. Pav
"""

import itertools
import random
from abc import ABC, abstractmethod
from collections import Counter
from math import prod

# the use of ^, |, & are subject to change...


class AbstractFiniteProbabilityDistribution(ABC):
    @property
    @abstractmethod
    def outcomes(self):
        pass

    @property
    @abstractmethod
    def probabilities(self):
        pass

    @property
    def len(self):
        return len(self.outcomes)

    @property
    def pmf_dict(self):
        return dict(zip(self.outcomes, self.probabilities))

    def pmf(self, x):
        return self.pmf_dict.get(x, 0)

    def sample(self, k):
        """
        generate a list of samples.
        """
        return random.choices(self.outcomes, weights=self.probabilities, k=k)

    def generate(self):
        """
        generate a single observation.
        """
        return self.sample(k=1)[0]

    def __mul__(self, other):
        """
        note that the _order_ of the outcomes matters.
        If it does not matter to you, use bitwise or; (should probably change that to the min)
        """
        if isinstance(other, int):
            multi_outcomes = [self.outcomes] * other
            multi_probabilities = [self.probabilities] * other
            new_outcomes = [sum(x) for x in list(itertools.product(*multi_outcomes))]
            new_probs = [prod(x) for x in itertools.product(*multi_probabilities)]
            return NumericalListProbabilityDistribution(
                outcomes=new_outcomes, weights=new_probs
            )
        else:
            new_outcomes = list(itertools.product(self.outcomes, other.outcomes))
            new_probs = [
                x[0] * x[1]
                for x in itertools.product(self.probabilities, other.probabilities)
            ]
            return ListProbabilityDistribution(outcomes=new_outcomes, weights=new_probs)

    def __rmul__(self, other):
        """
        other * rmul
        """
        return self.__mul__(other)

    def __pow__(self, other):
        if other < 0:
            raise ValueException(f"bad power {other}")
        if isinstance(other, int):
            multi_outcomes = [self.outcomes] * other
            multi_probabilities = [self.probabilities] * other
            new_outcomes = list(itertools.product(*multi_outcomes))
            new_probs = [prod(x) for x in itertools.product(*multi_probabilities)]
            return ListProbabilityDistribution(outcomes=new_outcomes, weights=new_probs)
        raise ValueException(f"bad power {other}")

    def __or__(self, other):
        """
        this is a multiplication, but order does not matter, so results are sorted
        """
        new_outcomes = [
            tuple(sorted(x))
            for x in list(itertools.product(self.outcomes, other.outcomes))
        ]
        new_probs = [
            x[0] * x[1]
            for x in itertools.product(self.probabilities, other.probabilities)
        ]
        return ListProbabilityDistribution.from_duplicated(new_outcomes, new_probs)

    def __xor__(self, other):
        """
        this is the max of the tuple of two probability distributions
        """
        new_outcomes = [
            max(x) for x in itertools.product(self.outcomes, other.outcomes)
        ]
        new_probs = [
            x[0] * x[1]
            for x in itertools.product(self.probabilities, other.probabilities)
        ]
        return ListProbabilityDistribution.from_duplicated(new_outcomes, new_probs)


class NumericalValuedFiniteProbabilityDistributionMixin:
    def expected_value(self, f=None):
        """
        Computes E[f(x)] for this x. f defaults to lambda x: x
        """
        if f is None:
            f = lambda x: x
        return sum([f(x) * p for x, p in zip(self.outcomes, self.probabilities)]) / sum(
            self.probabilities
        )

    def variance(self):
        """
        Computes VAR(x) for this x.
        """
        Ex = self.expected_value()
        Ex2 = self.expected_value(f=lambda x: x ** 2)
        return Ex2 - Ex ** 2

    def __add__(self, other):
        """
        Given two numerical valued distributions, return the distribution of the sum
        of independent realizations from the two.
        """
        new_outcomes = [
            sum(x) for x in list(itertools.product(self.outcomes, other.outcomes))
        ]
        new_probs = [
            x[0] * x[1]
            for x in itertools.product(self.probabilities, other.probabilities)
        ]
        return NumericalListProbabilityDistribution.from_duplicated(
            new_outcomes, new_probs
        )


class UniformDiscreteFiniteProbabilityDistribution(
    AbstractFiniteProbabilityDistribution
):
    def __init__(self, outcomes):
        self.__outcomes = outcomes

    @property
    def outcomes(self):
        return self.__outcomes

    @property
    def probabilities(self):
        nel = len(self.outcomes)
        return [1 / nel] * nel


class ListProbabilityDistribution(AbstractFiniteProbabilityDistribution):
    def __init__(self, outcomes, weights=None):
        """
        weights: default to equal weighting if None given.
        """
        self.__outcomes = outcomes
        if weights is None:
            nel = len(outcomes)
            weights = [1 / nel] * nel
        else:
            total_val = sum(weights)
            weights = [x / total_val for x in weights]
            assert (
                min(weights) >= 0
            ), f"expecting non-negative weights, got {min(weights)=}"
        assert len(outcomes) == len(
            weights
        ), f"expecting {len(outcomes)=}=={len(weights)=}"
        self.__weights = weights

    @property
    def outcomes(self):
        return self.__outcomes

    @property
    def probabilities(self):
        return self.__weights

    @classmethod
    def from_duplicated(cls, outcomes, weights):
        coco = Counter()
        for key, value in zip(outcomes, weights):
            coco.update({key: value})
        return cls(outcomes=list(coco.keys()), weights=list(coco.values()))

    @classmethod
    def certainty(cls, outcome):
        return cls(outcomes=[outcome], weights=[1])


class NumericalListProbabilityDistribution(
    NumericalValuedFiniteProbabilityDistributionMixin, ListProbabilityDistribution
):
    pass


class DiceProbabilityDistribution(
    NumericalValuedFiniteProbabilityDistributionMixin,
    UniformDiscreteFiniteProbabilityDistribution,
):
    def __init__(self, sides=6):
        super().__init__(list(range(sides)))
        self.__sides = sides

    @property
    def sides(self):
        return self.__sides


class UnfairDiceProbabilityDistribution(
    NumericalValuedFiniteProbabilityDistributionMixin, ListProbabilityDistribution
):
    def __init__(self, weights):
        super().__init__(list(range(len(weights))), weights)
        self.__sides = len(weights)

    @property
    def sides(self):
        return self.__sides


def test_some():
    a1 = NumericalListProbabilityDistribution.certainty(1)
    fooz = ListProbabilityDistribution(
        ["hearts", "diamonds", "clubs", "spades"], [1 / 4] * 4
    )
    barz = fooz * fooz
    zoop = fooz ** 2
    zoop = fooz ** 3
    fooz.pmf_dict
    uno = fooz | fooz
    dummy = fooz ^ fooz


def test_dice_run():
    twelve_sided = DiceProbabilityDistribution(12)
    assert sorted(twelve_sided.outcomes) == sorted(list(range(12)))
    three_twelves = 3 * twelve_sided
    three_twelves = twelve_sided * 3
    three_twelves.sample(20)
    sum_of_two = twelve_sided + twelve_sided
    sorted(sum_of_two.sample(100))
    best_of_two = twelve_sided ^ twelve_sided
    tworolls = twelve_sided * twelve_sided
    tworolls.sample(20)
    twotwo = twelve_sided ** 2


def test_unfair_dice_run():
    weirdo = UnfairDiceProbabilityDistribution(
        [1 / 2, 1 / 10, 1 / 10, 1 / 10, 1 / 10, 1 / 10]
    )
    weighted = weirdo * weirdo
    weirdo.expected_value()
    (weirdo + weirdo).expected_value()
    (weirdo + weirdo).variance()
    (weirdo + weirdo + weirdo).expected_value()
    (3 * weirdo).expected_value()


# for vim modeline: (do not edit)
# vim:ts=4:sw=4:sts=4:tw=79:sta:et:ai:nu:fdm=indent:syn=python:ft=python:tag=.py_tags;:cin:fo=croql
