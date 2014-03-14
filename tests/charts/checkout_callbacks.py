# coding: utf-8
from functools import wraps
from fsm.core import StateConditionError


BASKET_MAX_AMOUNT = 2


def fsm_proxy_data_required(fn):
    @wraps(fn)
    def callback(fsm_proxy):
        if not fsm_proxy.data:
            raise StateConditionError('Data is required for processing')
        return fn(fsm_proxy)
    return callback


def for_normal_users_only(fn):
    @wraps(fn)
    def callback(fsm_proxy):
        if fsm_proxy.data and 'user' in fsm_proxy.data:
            user = fsm_proxy.data['user']
            if user.is_banned():
                raise StateConditionError('Not for Mooducks')
        return fn(fsm_proxy)
    return callback


@fsm_proxy_data_required
def on_enter_in_busket(fsm_proxy):
    if fsm_proxy.event == 'do_add_to_busket':
        if not all((
            'product' in fsm_proxy.data,
            'basket' in fsm_proxy.data,
        )):
            raise StateConditionError(
                'Product and Basket instances are required'
            )

        basket = fsm_proxy.data['basket']
        product = fsm_proxy.data['product']
        if not product.is_available:
            raise StateConditionError('Product is not available to add')

        if basket.amount >= BASKET_MAX_AMOUNT:
            raise StateConditionError('Basket is full')


@fsm_proxy_data_required
def on_change_in_busket(fsm_proxy):
    if fsm_proxy.event == 'do_add_to_busket':
        basket = fsm_proxy.data['basket']
        product = fsm_proxy.data['product']
        basket.add(product)

    if fsm_proxy.event == 'do_remove_product':
        basket = fsm_proxy.data['basket']
        product = fsm_proxy.data['product']
        basket.remove(product)

    if basket.amount:
        fsm_proxy.fsm.send('~do_goto_full_busket', autosave=False)
    else:
        fsm_proxy.fsm.send('~do_goto_empty_busket', autosave=False)


@for_normal_users_only
def on_enter_in_frontpage(fsm_proxy):
    print('Trying to visit frontpage')


@for_normal_users_only
def on_change_in_frontpage(fsm_proxy):
    print('We are on the frontpage')


def on_exit_from_frontpage(fsm_proxy):
    if fsm_proxy.event == 'do_add_to_busket':
        print('Went to the busket from the frontpage')


@fsm_proxy_data_required
def on_change_in_product(fsm_proxy):
    product = fsm_proxy.data['product']
    if not product.is_available:
        fsm_proxy.fsm.send('~do_goto_in_product_unavailable', autosave=False)
    else:
        fsm_proxy.fsm.send('~do_goto_in_product_normal', autosave=False)


CUSTOM_CALLBACKS = {
    'in_busket': {
        'on_enter': on_enter_in_busket,
        'on_change': on_change_in_busket,
    },
    'in_frontpage': {
        'on_enter': on_enter_in_frontpage,
        'on_change': on_change_in_frontpage,
        'on_exit': on_exit_from_frontpage,
    },
    'in_product': {
        'on_change': on_change_in_product,
    }
}
