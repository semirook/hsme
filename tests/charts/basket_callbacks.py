# coding: utf-8


def on_enter_in_recalculation(fsm_proxy):
    pass


def on_change_in_recalculation(fsm_proxy):
    fsm_proxy.fsm.datamodel.update(fsm_proxy.data)


def on_exit_in_recalculation(fsm_proxy):
    pass


def on_change_in_basket_normal(fsm_proxy):
    pass


def on_enter_in_basket_freeze(fsm_proxy):
    pass
