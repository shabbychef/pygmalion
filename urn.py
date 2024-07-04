#! /usr/bin/env python
# coding: utf-8
#
"""
.. module pygmalion:: pygmalion
   :synopsis: Urn of objects you can select from.

.. moduleauthor: Steven E. Pav <steven@gilgamath.com>

    SVN: $Id$
    Created: 2024.06.14
    Copyright: Steven E. Pav, 2024
    Author: Steven E. Pav
    Comments: Steven E. Pav
"""

import itertools
import random
from math import factorial, comb, perm
from collections import Counter

class Urn(Counter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def perm_k(self, k:int=1):
        """
        A generator over k-tuples of elements selected without replacement from the given counts.
        This is a permutation generator, so the order matters.
        Returns the k tuples, the probability of selecting that k-tuple, and an Urn object
        with the items removed.
        """
        total_count = sum(self.values())
        assert k <= total_count, f"cannot permute {k=} objects from {total_count}"
        deno = perm(total_count, k)
        for atup in itertools.product(self.keys(), repeat=k):
            wt = 1
            acop = dict(self).copy()
            for av in atup:
                wt *= acop[av]
                acop[av] -= 1
            if wt != 0:
                yield (*atup, wt/deno, type(self)(acop))
    def _generate_(self):
        """
        pick one from the urn, returning the tail urn
        """
        choice = random.choices(list(self.keys()), weights=list(self.values()), k=1)
        acop = dict(self).copy()
        acop[choice[0]] -= 1
        return (choice, type(self)(acop))
    def sample(self, k:int=1, replace:bool=False):
        """
        Sample from the urn, possibly with replacement, returning a list.
        """
        retv = []
        tailself = self.copy()
        for idx in range(k):
            if replace:
                choice, _ = tailself._generate_()
            else:
                choice, tailself = tailself._generate_()
            retv.extend(choice)
        return retv


#for vim modeline: (do not edit)
# vim:ts=4:sw=4:sts=4:tw=79:sta:et:ai:nu:fdm=indent:syn=python:ft=python:tag=.py_tags;:cin:fo=croql
