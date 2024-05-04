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

from abc import ABC, abstractmethod
from collections import Counter
from math import prod
import random
import itertools

class DiscreteFiniteProbabilityDistribution(ABC):
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
        generate a list of samples
        """
        return random.choices(self.outcomes, weights=self.probabilities, k=k)
    def generate(self):
        """
        generate a single observation
        """
        return self.sample(k=1)[0]
    def __mul__(self, other):
        """
        note that the _order_ of the outcomes matters.
        If it does not matter to you, use bitwise or
        """
        if isinstance(other, int):
            multi_outcomes = [self.outcomes] * other
            multi_probabilities = [self.probabilities] * other
            new_outcomes = [sum(x) for x in list(itertools.product(*multi_outcomes))]
            new_probs = [prod(x) for x in itertools.product(*multi_probabilities)]
            return ListProbabilityDistribution(outcomes=new_outcomes, weights=new_probs)
        else:
            new_outcomes = list(itertools.product(self.outcomes, other.outcomes))
            new_probs = [x[0]*x[1] for x in itertools.product(self.probabilities, other.probabilities)]
            return ListProbabilityDistribution(outcomes=new_outcomes, weights=new_probs)
    def __pow__(self, other):
        if other<0:
            raise ValueException(f"bad power {other}")
        if isinstance(other, int):
            multi_outcomes = [self.outcomes] * other
            multi_probabilities = [self.probabilities] * other
            new_outcomes = list(itertools.product(*multi_outcomes))
            new_probs = [prod(x) for x in itertools.product(*multi_probabilities)]
            return ListProbabilityDistribution(outcomes=new_outcomes, weights=new_probs)
        raise ValueException(f"bad power {other}")
    def __add__(self, other):
        new_outcomes = [sum(x) for x in list(itertools.product(self.outcomes, other.outcomes))]
        new_probs = [x[0]*x[1] for x in itertools.product(self.probabilities, other.probabilities)]
        return ListProbabilityDistribution.from_duplicated(new_outcomes, new_probs)
    def __or__(self, other):
        """
        this is a multiplication, but order does not matter, so results are sorted
        """
        new_outcomes = [tuple(sorted(x)) for x in list(itertools.product(self.outcomes, other.outcomes))]
        new_probs = [x[0]*x[1] for x in itertools.product(self.probabilities, other.probabilities)]
        return ListProbabilityDistribution.from_duplicated(new_outcomes, new_probs)
    def __xor__(self, other):
        new_outcomes = [max(x) for x in itertools.product(self.outcomes, other.outcomes)]
        new_probs = [x[0]*x[1] for x in itertools.product(self.probabilities, other.probabilities)]
        return ListProbabilityDistribution.from_duplicated(new_outcomes, new_probs)

class UniformDiscreteFiniteProbabilityDistribution(DiscreteFiniteProbabilityDistribution):
    def __init__(self, outcomes):
        self.__outcomes = outcomes
    @property
    def outcomes(self):
        return self.__outcomes
    @property
    def probabilities(self):
        nel = len(self.outcomes)
        return [1/nel]*nel

class ListProbabilityDistribution(DiscreteFiniteProbabilityDistribution):
    def __init__(self, outcomes, weights=None):
        """
        weights: default to equal weighting if None given.
        """
        self.__outcomes = outcomes
        if weights is None:
            nel = len(outcomes)
            weights = [1/nel]*nel
        else:
            total_val = sum(weights)
            weights = [x/total_val for x in weights]
            assert min(weights) >= 0, f"expecting non-negative weights, got {min(weights)=}"
        assert len(outcomes)==len(weights), f"expecting {len(outcomes)=}=={len(weights)=}"
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
            coco.update({key:value})
        return cls(outcomes=list(coco.keys()), weights=list(coco.values()))


        
fooz = ListProbabilityDistribution(['hearts','diamonds','clubs','spades'],[1/4]*4)

barz = fooz * fooz
zoop = fooz**2
zoop = fooz**3


fooz.pmf_dict
uno = fooz | fooz


dummy = fooz ^ fooz

class DiceProbabilityDistribution(UniformDiscreteFiniteProbabilityDistribution):
    def __init__(self, sides=6):
        super().__init__(list(range(sides)))
        self.__sides = sides
    @property
    def sides(self):
        return self.__sides

class UnfairDiceProbabilityDistribution(ListProbabilityDistribution):
    def __init__(self, weights):
        super().__init__(list(range(len(weights))), weights)
        self.__sides = len(weights)
    @property
    def sides(self):
        return self.__sides


blah = DiceProbabilityDistribution(12)

dude = blah*3
dude = 3 * blah

blah.sample(20)

sum_of_two = blah + blah
sorted(sum_of_two.sample(100))

blah

best_of_two = blah^blah

tworolls = blah*blah
tworolls.sample(20)

maxo = blah ^ blah

twotwo = blah**2


weirdo = UnfairDiceProbabilityDistribution([1/2, 1/10, 1/10, 1/10, 1/10, 1/10])

weighted = weirdo*weirdo

# do we want a discrete probability distribution where the outcomes are numeric?
def expected_value(probdist: DiscreteFiniteProbabilityDistribution):
    return sum([x*p for x,p in zip(probdist.outcomes, probdist.probabilities)]) / sum(probdist.probabilities)

expected_value(weirdo)
expected_value(weirdo + weirdo)
expected_value(weirdo + weirdo + weirdo)



#for vim modeline: (do not edit)
# vim:ts=4:sw=4:sts=4:tw=79:sta:et:ai:nu:fdm=indent:syn=python:ft=python:tag=.py_tags;:cin:fo=croql
