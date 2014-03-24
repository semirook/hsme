# coding: utf-8
import os
import unittest
from functools import partial
from mock import patch
from fsm.core import (
    HSMERunner,
    ImpossibleEventError,
    UnregisteredEventError,
    StateConditionError,
)
from fsm.parsers import HSMEDictsParser, HSMEXMLParser
from .charts.checkout import SIMPLE_CHECKOUT
from .charts.checkout_callbacks import CUSTOM_CALLBACKS
from .charts.basket_another_callbacks import on_enter_in_recalculation_another
from .factories import Basket, Product


class CommonTests(unittest.TestCase):

    def test_initial_state(self):
        hsme = HSMERunner()
        checkout_sm = HSMEDictsParser(SIMPLE_CHECKOUT).parse()
        hsme.load(checkout_sm, autosave=False)
        hsme.start(autosave=False)
        transitions = SIMPLE_CHECKOUT[0]['events']
        self.assertTrue(hsme.get_possible_transitions() == transitions)
        self.assertTrue(hsme.in_state('in_frontpage'))
        self.assertTrue(hsme.is_initial())

    def test_transitions_from_initial(self):
        hsme = HSMERunner()
        checkout_sm = HSMEDictsParser(SIMPLE_CHECKOUT).parse()
        hsme.load(checkout_sm, autosave=False)
        hsme.start(autosave=False)
        sender = partial(hsme.send, autosave=False)

        with self.assertRaises(ImpossibleEventError):
            sender('do_create_order')
        with self.assertRaises(UnregisteredEventError):
            sender('do_something_strange')

        sender('do_goto_product_page')
        self.assertTrue(hsme.current_state.name == 'in_product')

        sender('~do_goto_in_product_normal')  # internal event
        self.assertTrue(hsme.can_send('do_add_to_busket'))
        self.assertFalse(hsme.can_send('do_something_strange'))

        sender('do_add_to_busket')
        self.assertTrue(hsme.current_state.name == 'in_busket')

        sender('~do_goto_full_busket')  # internal event
        sender('do_create_order')
        self.assertTrue(hsme.is_finished())

    def test_different_sc_instances(self):
        hsme = HSMERunner()
        checkout_sm_1 = HSMEDictsParser(SIMPLE_CHECKOUT).parse()
        checkout_sm_2 = HSMEDictsParser(SIMPLE_CHECKOUT).parse()
        hsme.load(checkout_sm_1, autosave=False).start(autosave=False)
        sender = partial(hsme.send, autosave=False)

        sender('do_goto_busket', autosave=False)
        self.assertTrue(hsme.current_state.name == 'in_busket')

        hsme.load(checkout_sm_2, autosave=False).start(autosave=False)
        self.assertTrue(hsme.current_state.name == 'in_frontpage')

    def test_transitions_with_callbacks(self):
        hsme = HSMERunner()
        checkout_sm = HSMEDictsParser(SIMPLE_CHECKOUT).parse()
        hsme.load(checkout_sm, autosave=False)
        hsme.register_processing_map(CUSTOM_CALLBACKS)
        hsme.start(autosave=False)
        sender = partial(hsme.send, autosave=False)

        my_basket = Basket()
        selected_product = Product.produce_normal()

        sender(
            'do_add_to_busket', data={
                'product': selected_product,
                'basket': my_basket,
            }
        )
        self.assertTrue(hsme.current_state.name == 'in_busket_normal')
        self.assertTrue(my_basket.amount == 1)

        sender(
            'do_remove_product', data={
                'product': selected_product,
                'basket': my_basket,
            }
        )
        self.assertTrue(hsme.current_state.name == 'in_busket_empty')
        self.assertTrue(my_basket.amount == 0)

        sender('do_goto_frontpage')
        self.assertTrue(hsme.current_state.name == 'in_frontpage')

    def test_transitions_with_errors(self):
        hsme = HSMERunner()
        checkout_sm = HSMEDictsParser(SIMPLE_CHECKOUT).parse()
        hsme.load(checkout_sm, autosave=False)
        hsme.register_processing_map(CUSTOM_CALLBACKS)
        hsme.start(autosave=False)
        sender = partial(hsme.send, autosave=False)

        my_basket = Basket()
        product_1 = Product.produce_normal()

        sender(
            'do_add_to_busket', data={
                'product': product_1,
                'basket': my_basket,
            }
        )
        self.assertTrue(my_basket.amount == 1)
        sender('do_goto_product_page', data={'product': product_1})

        product_2 = Product.produce_normal()
        sender(
            'do_add_to_busket', data={
                'product': product_2,
                'basket': my_basket,
            }
        )

        self.assertTrue(my_basket.amount == 2)
        self.assertTrue(hsme.current_state.name == 'in_busket_normal')
        sender('do_goto_product_page', data={'product': product_2})

        product_3 = Product.produce_normal()
        with self.assertRaises(StateConditionError):
            sender(
                'do_add_to_busket', data={
                    'product': product_3,
                    'basket': my_basket,
                }
            )
        self.assertTrue(my_basket.amount == 2)
        self.assertTrue(hsme.current_state.name == 'in_product_normal')

        sender('do_goto_frontpage')
        self.assertTrue(hsme.current_state.name == 'in_frontpage')


def get_xml_path():
    ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(ROOT_PATH, 'charts', 'basket.xml')
    return path


class TestCallbacks(unittest.TestCase):

    @patch('tests.charts.basket_callbacks.on_change_in_basket_normal')
    @patch('tests.charts.basket_callbacks.on_exit_in_recalculation')
    @patch('tests.charts.basket_callbacks.on_change_in_recalculation')
    @patch('tests.charts.basket_callbacks.on_enter_in_recalculation')
    def test_initial_state(self, enter_mock, change_mock, exit_mock, change_b_mock):
        hsme = HSMERunner()
        xml_path = get_xml_path()
        checkout_sm = HSMEXMLParser.parse_from_path(xml_path)
        hsme.load(checkout_sm, autosave=False)
        hsme.start(autosave=False)

        self.assertFalse(enter_mock.called)
        self.assertFalse(change_mock.called)
        self.assertFalse(exit_mock.called)

        hsme.send('do_add_to_basket', autosave=False)
        self.assertTrue(enter_mock.called)
        self.assertTrue(change_mock.called)
        self.assertFalse(exit_mock.called)

        hsme.send('do_goto_in_basket_normal', autosave=False)
        self.assertTrue(exit_mock.called)
        self.assertTrue(change_b_mock.called)

    @patch('tests.charts.basket_callbacks.on_enter_in_recalculation')
    def test_registered_callbacks(self, enter_mock_1):
        hsme = HSMERunner()
        xml_path = get_xml_path()
        checkout_sm = HSMEXMLParser.parse_from_path(xml_path)
        hsme.load(checkout_sm, autosave=False)
        hsme.register_processing_map({
            'in_recalculation': {
                'on_enter': on_enter_in_recalculation_another
            }
        })
        hsme.start(autosave=False)

        hsme.send('do_add_to_basket', autosave=False)
        self.assertFalse(enter_mock_1.called)
