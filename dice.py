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

import copy
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

    def __mod__(self, other):
        """
        This computes the 'modulo' operator, which returns two independent draws
        from the two distributions, returning tuples.  Order matters.
        If id(self) == id(other)??
        """
        if isinstance(other, int):
            multi_outcomes = [self.outcomes] * other
            multi_probabilities = [self.probabilities] * other
            new_outcomes = [sum(x) for x in list(itertools.product(*multi_outcomes))]
            new_probs = [prod(x) for x in itertools.product(*multi_probabilities)]
            return NumericalFiniteProbabilityDistribution(
                outcomes=new_outcomes, weights=new_probs
            )
        else:
            new_outcomes = list(itertools.product(self.outcomes, other.outcomes))
            new_probs = [
                x[0] * x[1]
                for x in itertools.product(self.probabilities, other.probabilities)
            ]
            return FiniteProbabilityDistribution(
                outcomes=new_outcomes, weights=new_probs
            )

    def __or__(self, other):
        """
        this is tuple, but order does not matter, so results are sorted
        should change so that or is max, and is min and something else is % + sorted.
        """
        new_outcomes = [
            tuple(sorted(x))
            for x in list(itertools.product(self.outcomes, other.outcomes))
        ]
        new_probs = [
            x[0] * x[1]
            for x in itertools.product(self.probabilities, other.probabilities)
        ]
        return FiniteProbabilityDistribution.from_duplicated(new_outcomes, new_probs)

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
        return FiniteProbabilityDistribution.from_duplicated(new_outcomes, new_probs)

    @abstractmethod
    def __copy__(self):
        pass

    @abstractmethod
    def __deepcopy__(self, memo):
        pass


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
        Given a numerical valued distribution, if you sum it with itself,
        return twice the value of the output. Here self is determined by object id.

        Otherwise, given two distinct numerical valued distributions (not the same id),
        return the distribution of the sum of independent realizations from the two.
        """
        if id(self) == id(other):
            return self.map(lambda x: 2 * x)
        else:
            new_outcomes = [
                sum(x) for x in list(itertools.product(self.outcomes, other.outcomes))
            ]
            new_probs = [
                x[0] * x[1]
                for x in itertools.product(self.probabilities, other.probabilities)
            ]
            return NumericalFiniteProbabilityDistribution.from_duplicated(
                new_outcomes, new_probs
            )

    def __mul__(self, other):
        """
        Given a numerical valued distribution, if you take the product with a float or int,
        you get the value scaled up by that amount.

        if you compute the product with itself, you get the values squared.

        if you take the product of two independent distributions, you get the distribution of their product.
        """
        if id(self) == id(other):
            return self.map(lambda x: x ** 2)
        elif isinstance(other, (int, float)):
            return self.map(lambda x: other * x)
        else:
            new_outcomes = [
                prod(x) for x in list(itertools.product(self.outcomes, other.outcomes))
            ]
            new_probs = [
                x[0] * x[1]
                for x in itertools.product(self.probabilities, other.probabilities)
            ]
            return NumericalFiniteProbabilityDistribution.from_duplicated(
                new_outcomes, new_probs
            )

    def __rmul__(self, other):
        """
        other * rmul
        """
        return self.__mul__(other)

    def __pow__(self, other):
        if id(self) == id(other):
            return self.map(lambda x: x ** x)
        elif isinstance(other, (int, float)):
            return self.map(lambda x: x ** other)
        else:
            new_outcomes = [
                x[0] ** x[1]
                for x in list(itertools.product(self.outcomes, other.outcomes))
            ]
            new_probs = [
                x[0] * x[1]
                for x in itertools.product(self.probabilities, other.probabilities)
            ]
            return NumericalFiniteProbabilityDistribution.from_duplicated(
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

    def __copy__(self):
        return UniformDiscreteFiniteProbabilityDistribution(self.outcomes)

    def __deepcopy__(self, memo):
        return UniformDiscreteFiniteProbabilityDistribution(
            copy.deepcopy(self.outcomes)
        )


class FiniteProbabilityDistribution(AbstractFiniteProbabilityDistribution):
    def __init__(self, outcomes, weights=None):
        """
        weights: default to equal weighting if None given.
        """
        if outcomes is None and weights is not None:
            outcomes = list(range(len(weights)))
        self.__outcomes = outcomes
        if weights is None:
            nel = len(outcomes)
            weights = [1 / nel] * nel
        else:
            assert (
                min(weights) >= 0
            ), f"expecting non-negative weights, got {min(weights)=}"
            total_weight = sum(weights)
            assert total_weight > 0, "expecting some positive weights, got none"
            weights = [x / total_weight for x in weights]
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

    def __copy__(self):
        return type(self)(self.outcomes, self.probabilities)

    def __deepcopy__(self, memo):
        return type(self)(
            copy.deepcopy(self.outcomes), copy.deepcopy(self.probabilities)
        )

    def __eq__(self, other):
        if id(self) == id(other):
            return True
        self_dict = self.pmf_dict
        other_dict = other.pmf_dict
        for key, value in self_dict.items():
            if other_dict.get(key, 0) != value:
                return False
        for key, value in other_dict.items():
            if self_dict.get(key, 0) != value:
                return False
        return True

    def map(self, f):
        return type(self).from_duplicated(
            outcomes=map(f, self.outcomes), weights=self.probabilities
        )

    @classmethod
    def from_dict(cls, pmf_dict):
        return cls(outcomes=list(pmf_dict.keys()), weights=list(pmf_dict.values()))

    @classmethod
    def from_duplicated(cls, outcomes, weights):
        coco = Counter()
        for key, value in zip(outcomes, weights):
            coco.update({key: value})
        return cls(outcomes=list(coco.keys()), weights=list(coco.values()))

    @classmethod
    def certainty(cls, outcome):
        return cls(outcomes=[outcome], weights=[1])


class NumericalFiniteProbabilityDistribution(
    NumericalValuedFiniteProbabilityDistributionMixin, FiniteProbabilityDistribution
):
    pass


def DiceProbabilityDistribution(sides):
    return NumericalFiniteProbabilityDistribution(
        outcomes=list(range(sides)), weights=[1 / sides] * sides
    )


def UnfairDiceProbabilityDistribution(weights):
    return NumericalFiniteProbabilityDistribution(
        outcomes=list(range(len(weights))), weights=weights
    )


def test_list():
    agen = FiniteProbabilityDistribution(["hearts", "diamonds", "spades", "clubs"])
    assert agen.generate() in agen.outcomes
    for asample in agen.sample(100):
        assert asample in agen.outcomes
    assert agen == agen
    bgen = copy.copy(agen)
    assert agen == bgen
    cgen = FiniteProbabilityDistribution(list(reversed(agen.outcomes)))
    assert agen == cgen


def test_some():
    a1 = NumericalFiniteProbabilityDistribution.certainty(1)
    fooz = FiniteProbabilityDistribution(
        ["hearts", "diamonds", "clubs", "spades"], [1 / 4] * 4
    )
    barz = fooz % fooz


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
