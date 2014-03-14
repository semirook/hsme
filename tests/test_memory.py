# coding: utf-8
import time
from nose.tools import istest
from memory_profiler import profile
from fsm.core import HSMERunner
from fsm.parsers import HSMEDictsParser
from .charts.checkout import SIMPLE_CHECKOUT


MULTIPLE_AMOUNT = 1000


class Timer(object):

    def __init__(self, verbose=False):
        self.verbose = verbose

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.secs = self.end - self.start
        self.msecs = self.secs * 1000
        if self.verbose:
            print 'Elapsed time: %f ms' % self.msecs

        return self.msecs


@istest
@profile
def test_single_sc_instance_loading():
    with Timer() as t:
        hsme = HSMERunner()
        checkout_sm = HSMEDictsParser(SIMPLE_CHECKOUT)
        hsme.load(checkout_sm, autosave=False)
    print 'Single SC loading: %f ms' % (t.msecs)


@istest
def test_multiple_sc_instances_loading():
    with Timer() as t:
        hsme = HSMERunner()
        checkout_sm = (
            HSMEDictsParser(SIMPLE_CHECKOUT).parse()
            for x in xrange(MULTIPLE_AMOUNT)
        )
        for c in checkout_sm:
            hsme.load(c, autosave=False)
    print '%d SC instances loading: %f ms' % (MULTIPLE_AMOUNT, t.msecs)
