# coding: utf-8
import unittest
from functools import partial
from fsm.core import HSMERunner, StateConditionError
from fsm.parsers import HSMEDictsParser
from .charts.checkout import SIMPLE_CHECKOUT
from .charts.checkout_callbacks import for_normal_users_only
from .factories import (
    User,
    DataStore,
    Basket,
    Product,
)


@for_normal_users_only
def on_enter_in_busket_data(fsm_proxy):
    if fsm_proxy.event == 'do_add_to_busket':
        datamodel = fsm_proxy.fsm.datamodel
        basket = datamodel['BASKET_INSTANCE']
        product = fsm_proxy.data['product']
        if basket.amount >= datamodel['BASKET_MAX_AMOUNT']:
            raise StateConditionError('Basket is full')
        if basket.same_product_count(product) >= datamodel['PRODUCT_MAX_AMOUNT']:
            raise StateConditionError('Product riched maximum amount')


@for_normal_users_only
def on_change_in_busket_data(fsm_proxy):
    basket = fsm_proxy.fsm.datamodel['BASKET_INSTANCE']
    if fsm_proxy.event == 'do_add_to_busket':
        product = fsm_proxy.data['product']
        basket.add(product)

    if fsm_proxy.event == 'do_remove_product':
        product = fsm_proxy.data['product']
        basket.remove(product)

    if basket.amount:
        fsm_proxy.fsm.send('~do_goto_full_busket', autosave=False)
    else:
        fsm_proxy.fsm.send('~do_goto_empty_busket', autosave=False)


def on_enter_in_order_info_processing(fsm_proxy):
    basket = fsm_proxy.fsm.datamodel['BASKET_INSTANCE']
    if basket.total_cost() < fsm_proxy.fsm.datamodel['MINIMAL_DELIVERY_COST']:
        raise StateConditionError('You need more buyings')
    for product in basket:
        product.is_available = False


def on_change_in_product(fsm_proxy):
    product = fsm_proxy.data['product']
    if product.is_reserved:
        fsm_proxy.fsm.send('~do_goto_in_product_reserved', autosave=False)

    if product.is_available:
        fsm_proxy.fsm.send('~do_goto_in_product_normal', autosave=False)
    else:
        fsm_proxy.fsm.send('~do_goto_in_product_unavailable', autosave=False)


CHECKOUT_CALLBACKS = {
    'in_busket': {
        'on_enter': on_enter_in_busket_data,
        'on_change': on_change_in_busket_data,
    },
    'in_order_info_processing': {
        'on_enter': on_enter_in_order_info_processing,
    },
    'in_product': {
        'on_change': on_change_in_product,
    }
}


class ComplexFlowTests(unittest.TestCase):

    def setUp(self):
        self.hsme = HSMERunner()
        self.hsme.send = partial(self.hsme.send, autosave=False)
        self.datastore = DataStore()
        for u in xrange(1, 5):
            product = Product.produce_normal(u)
            self.datastore.add_product(product)

            normal_user_sm = HSMEDictsParser(
                doc=SIMPLE_CHECKOUT,
                doc_id='checkout',
                datamodel=self._get_normal_user_datamodel(),
            ).parse()
            self.hsme.load(normal_user_sm, autosave=False)

            user = User.produce_normal(u)
            user.add_state_machine(
                sm_type=self.hsme.statechart_id,
                sm_pickle=self.hsme.pickle()
            )
            self.datastore.add_user(user)
            self.hsme.clear()

    def _get_normal_user_datamodel(self):
        normal_user_datamodel = {
            'BASKET_INSTANCE': Basket(),
            'BASKET_MAX_AMOUNT': 2,
            'PRODUCT_MAX_AMOUNT': 3,
            'MINIMAL_DELIVERY_COST': 100,
            'STOCK_COEFF': 0.3,
        }
        return normal_user_datamodel

    def test_story_of_two(self):
        # Let it be checkout process
        # and request came with user_id == 1
        user = self.datastore.get_user(1)
        sm_pickle = user.get_state_machine('checkout')

        self.assertFalse(self.hsme.is_loaded())
        self.assertFalse(self.hsme.is_started())

        self.hsme.load(sm_pickle, autosave=False)
        self.hsme.register_processing_map(CHECKOUT_CALLBACKS)

        self.assertTrue(self.hsme.is_loaded())
        self.assertFalse(self.hsme.is_started())

        self.hsme.start(data={'user': user}, autosave=False)

        self.assertTrue(self.hsme.is_started())
        self.assertTrue(self.hsme.is_initial())
        self.assertTrue(self.hsme.current_state.name == 'in_frontpage')

        self.hsme.send('do_goto_busket')
        self.assertTrue(self.hsme.current_state.name == 'in_busket_empty')
        user.add_state_machine('checkout', self.hsme.pickle())

        # Let it be checkout process
        # and request came with user_id == 2
        another_user = self.datastore.get_user(2)
        sm_pickle = another_user.get_state_machine('checkout')

        self.hsme.load(sm_pickle, autosave=False)
        self.hsme.register_processing_map(CHECKOUT_CALLBACKS)

        self.assertTrue(self.hsme.is_loaded())
        self.assertFalse(self.hsme.is_started())

        self.hsme.start(data={'user': another_user}, autosave=False)
        self.assertTrue(self.hsme.current_state.name == 'in_frontpage')
        another_user.add_state_machine('checkout', self.hsme.pickle())

        # Let it be checkout process
        # and request came with user_id == 1
        user = self.datastore.get_user(1)
        sm_pickle = user.get_state_machine('checkout')

        self.hsme.load(sm_pickle, autosave=False)
        self.hsme.register_processing_map(CHECKOUT_CALLBACKS)

        self.assertTrue(self.hsme.is_loaded())
        self.assertTrue(self.hsme.is_started())

        # We are in the state we left before
        self.assertTrue(self.hsme.current_state.name == 'in_busket_empty')

        self.hsme.send('do_goto_frontpage', data={'user': user})

        selected_product = self.datastore.get_product(3)
        self.hsme.send(
            'do_add_to_busket', data={
                'user': user,
                'product': selected_product,
            }
        )

        self.assertTrue(self.hsme.current_state.name == 'in_busket_normal')

        # Only 1 product is there, we need more
        with self.assertRaises(StateConditionError):
            self.hsme.send('do_create_order')

        self.assertTrue(self.hsme.current_state.name == 'in_busket_normal')
        self.hsme.send('do_goto_frontpage')

        selected_product = self.datastore.get_product(3)
        self.hsme.send(
            'do_add_to_busket', data={
                'user': user,
                'product': selected_product,
            }
        )
        self.hsme.send(
            'do_goto_product_page', data={
                'user': user,
                'product': selected_product,
            }
        )
        self.assertTrue(self.hsme.current_state.name == 'in_product_normal')

        # Maximum in busket is reached
        with self.assertRaises(StateConditionError):
            self.hsme.send(
                'do_add_to_busket', data={
                    'user': user,
                    'product': selected_product,
                }
            )

        self.hsme.send('do_goto_busket')
        self.hsme.send('do_create_order')

        # First user has finished
        self.assertTrue(self.hsme.is_finished())
        user.add_state_machine('checkout', self.hsme.pickle())

        another_user = self.datastore.get_user(2)
        sm_pickle = another_user.get_state_machine('checkout')
        self.hsme.load(sm_pickle, autosave=False)
        self.hsme.register_processing_map(CHECKOUT_CALLBACKS)

        self.assertTrue(self.hsme.current_state.name == 'in_frontpage')

        selected_product = self.datastore.get_product(3)
        self.hsme.send(
            'do_goto_product_page', data={
                'user': another_user,
                'product': selected_product,
            }
        )
        # Due to it was ordered by another user
        self.assertTrue(self.hsme.current_state.name == 'in_product_unavailable')
        # And this user can't buy it
        self.assertFalse(self.hsme.can_send('do_add_to_busket'))
        another_user.add_state_machine('checkout', self.hsme.pickle())
