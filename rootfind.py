#! /usr/bin/env python
# coding: utf-8
#
"""
.. module pygmalion:: 
   :synopsis: root finding routines

.. moduleauthor: Steven E. Pav <steven@gilgamath.com>
    
    Root finding routines. 
    See https://numbersandshapes.net/posts/illinois_pegasus_methodss/

    Created: 2024.07.31
    Copyright: Steven E. Pav, 2024
    Author: Steven E. Pav
    Comments: Steven E. Pav
"""

def illinois_method(f, a, b, fa=None, fb=None, max_iter=1000, xtol=1e-15, ytol=1e-15, verbosity=0):
    iter = 0
    if fa is None:
        fa = f(a)
        iter += 1
    if fb is None:
        fb = f(b)
        iter += 1
    assert fa*fb <= 0, "values do not bracket a root?"
    converged = (abs(a-b) < xtol) or (iter > max_iter)
    while not converged:
        c = b - fb*(b-a)/(fb-fa)
        fc = f(c)
        iter += 1
        if fb*fc < 0:
            a, fa = (b, fb)
        else:
            fa = fa/2
        b, fb = (c, fc)
        if verbosity > 0:
            print(f"{iter}: {a}, {b}, {c}, {abs(a-b)}")
        converged = (abs(a-b) < xtol) or (abs(fb) < ytol) or (iter > max_iter)
    return c


def bisect_method(f, a, b, fa=None, fb=None, max_iter=1000, xtol=1e-15, ytol=1e-15, verbosity=0):
    iter = 0
    if fa is None:
        fa = f(a)
        iter += 1
    if fb is None:
        fb = f(b)
        iter += 1
    assert fa*fb <= 0, "values do not bracket a root?"
    converged = (abs(a-b) < xtol) or (iter > max_iter)
    while not converged:
        c = 0.5 * (a + b)
        fc = f(c)
        iter += 1
        if fb*fc < 0:
            a, fa = (c, fc)
        else:
            b, fb = (c, fc)
        if verbosity > 0:
            print(f"{iter}: {a}, {b}, {c}, {abs(a-b)}")
        converged = (abs(a-b) < xtol) or (abs(fb) < ytol) or (iter > max_iter)
    return c


def secant_method(f, a, b, fa=None, fb=None, max_iter=1000, xtol=1e-15, ytol=1e-15, verbosity=0):
    iter = 0
    if fa is None:
        fa = f(a)
        iter += 1
    if fb is None:
        fb = f(b)
        iter += 1
    xm2, ym2 = (a, fa)
    xm1, ym1 = (b, fb)
    converged = (abs(xm2-xm1) < xtol) or (abs(ym2) < ytol) or (iter > max_iter)
    while not converged:
        x0 = (xm2*ym1 - xm1*ym2) / (ym1 - ym2)
        y0 = f(x0)
        iter += 1
        if verbosity > 0:
            print(f"{iter}: {xm2}, {xm1}, {x0}, {abs(xm1-x0)}")
        converged = (abs(xm1-x0) < xtol) or (abs(y0) < ytol) or (iter > max_iter)
        xm2, ym2, xm1, ym1 = (xm1, ym1, x0, y0)
    return x0

def false_pos_method(f, a, b, fa=None, fb=None, max_iter=1000, xtol=1e-15, ytol=1e-15, verbosity=0):
    iter = 0
    if fa is None:
        fa = f(a)
        iter += 1
    if fb is None:
        fb = f(b)
        iter += 1
    xm2, ym2 = (a, fa)
    xm1, ym1 = (b, fb)
    converged = (abs(xm2-xm1) < xtol) or (abs(ym2) < ytol) or (iter > max_iter)
    while not converged:
        x0 = (xm2*ym1 - xm1*ym2) / (ym1 - ym2)
        y0 = f(x0)
        if ym1 * y0 < 0:
            xm2, ym2 = (xm1, ym1)
        iter += 1
        if verbosity > 0:
            print(f"{iter}: {xm2}, {xm1}, {x0}, {abs(xm1-x0)}")
        converged = (abs(xm1-x0) < xtol) or (abs(y0) < ytol) or (iter > max_iter)
        xm1, ym1 = (x0, y0)
    return x0


def test_all():
    import math
    fx = lambda x:0.05 + 0.9*math.sqrt(x) - (1 - x)
    a, b = (0, 1)
    print("### illinois: ")
    illinois_method(fx, a, b, verbosity=1)
    print("### bisect: ")
    bisect_method(fx, a, b, verbosity=1)
    print("### secant: ")
    secant_method(fx, a, b, verbosity=1)
    print("### false pos: ")
    false_pos_method(fx, a, b, verbosity=1)


#for vim modeline: (do not edit)
# vim:ts=4:sw=4:sts=4:tw=79:sta:et:ai:nu:fdm=indent:syn=python:ft=python:tag=.py_tags;:cin:fo=croql
