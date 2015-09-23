# coding: utf-8
import os
import sys
import unittest


PY = sys.version_info
PY3K = PY >= (3, 0, 0)


if PY3K:
    from unittest import mock
else:
    import mock

from functools import partial
from fsm.core import (
    HSMERunner,
    ImpossibleEventError,
    UnregisteredEventError,
    StateConditionError,
)
from fsm.parsers import HSMEDictsParser, HSMEXMLParser
from .charts.basket import BASKET_CHART


def get_basket_xml_path():
    ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(ROOT_PATH, 'charts', 'basket.xml')
    return path


class TestBasics(unittest.TestCase):

    def test_initial_state(self):
        hsme = HSMERunner()
        basket_sm = HSMEDictsParser(BASKET_CHART).parse()
        hsme.load(basket_sm)
        hsme.start()
        transitions = BASKET_CHART[-1]['events']
        self.assertTrue(hsme.get_possible_transitions() == transitions)
        self.assertTrue(hsme.in_state('in_basket_empty'))
        self.assertTrue(hsme.is_initial())

    def test_transitions_from_initial(self):
        hsme = HSMERunner()
        basket_sm = HSMEDictsParser(BASKET_CHART).parse()
        hsme.load(basket_sm)
        hsme.start()

        with self.assertRaises(UnregisteredEventError):
            hsme.send('do_something_strange')

        hsme.send('do_add_to_basket')
        self.assertTrue(hsme.current_state.name == 'in_recalculation')

        hsme.send('do_goto_in_basket_normal')  # internal event
        self.assertTrue(hsme.can_send('do_add_to_basket'))
        self.assertFalse(hsme.can_send('do_something_strange'))


class TestCallbacks(unittest.TestCase):

    @mock.patch('tests.charts.basket_callbacks.on_change_in_basket_normal')
    @mock.patch('tests.charts.basket_callbacks.on_exit_in_recalculation')
    @mock.patch('tests.charts.basket_callbacks.on_change_in_recalculation')
    @mock.patch('tests.charts.basket_callbacks.on_enter_in_recalculation')
    def test_initial_state(self, enter_mock, change_mock, exit_mock, change_b_mock):
        hsme = HSMERunner()
        xml_path = get_basket_xml_path()
        checkout_sm = HSMEXMLParser.parse_from_path(xml_path)
        hsme.load(checkout_sm)
        hsme.start()

        self.assertFalse(enter_mock.called)
        self.assertFalse(change_mock.called)
        self.assertFalse(exit_mock.called)

        hsme.send('do_add_to_basket')
        self.assertTrue(enter_mock.called)
        self.assertTrue(change_mock.called)
        self.assertFalse(exit_mock.called)

        hsme.send('do_goto_in_basket_normal')
        self.assertTrue(exit_mock.called)
        self.assertTrue(change_b_mock.called)

    def test_datamodel_change(self):
        hsme = HSMERunner()
        xml_path = get_basket_xml_path()
        checkout_sm = HSMEXMLParser.parse_from_path(xml_path)
        hsme.load(checkout_sm)
        hsme.start()

        add_data = {'id': 1, 'name': 'Stuff', 'count': 5}
        hsme.send('do_add_to_basket', add_data)
        self.assertDictEqual(add_data, hsme.datamodel)

    def test_save_and_load(self):
        hsme = HSMERunner()
        xml_path = get_basket_xml_path()
        checkout_sm = HSMEXMLParser.parse_from_path(xml_path)
        hsme.load(checkout_sm)
        hsme.start()

        add_data = {'id': 2, 'name': 'Marshmallow', 'count': 100}
        hsme.send('do_add_to_basket', add_data)

        pickled_sm = hsme.save()
        hsme.clear()

        self.assertFalse(hsme.is_loaded())
        self.assertFalse(hsme.is_started())

        hsme.load(pickled_sm)
        self.assertTrue(hsme.is_loaded())
        self.assertTrue(hsme.is_started())

        self.assertDictEqual(add_data, hsme.datamodel)
