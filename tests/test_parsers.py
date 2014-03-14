# coding: utf-8
import os
from fsm.parsers import HSMEXMLParser
from unittest import TestCase


def get_xml_path():
    ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(ROOT_PATH, 'charts', 'basket.xml')
    return path


class TestXMLParser(TestCase):

    def test_transitions(self):
        path = get_xml_path()
        with open(path) as xml:
            parser = HSMEXMLParser(xml)
            table = parser.parse()

        self.assertEqual(table._init_state.name, 'in_basket_empty')
        statechart = table._statechart

        events = {
            'do_goto_in_basket_empty',
            'do_goto_in_basket_normal',
            'do_goto_in_basket_freeze',
            'do_add_to_basket',
            'do_remove_product',
        }
        self.assertSetEqual(set(statechart.keys()), events)

        transitions = statechart['do_goto_in_basket_empty']
        self.assertTrue(len(transitions) == 1)
        src, dst = transitions.items()[0]
        self.assertEqual(src.name, 'in_recalculation')
        self.assertEqual(dst.name, 'in_basket_empty')

        transitions = statechart['do_goto_in_basket_normal']
        self.assertTrue(len(transitions) == 2)
        self.assertSetEqual(
            {x.name for x in transitions},
            {'in_basket_normal', 'in_recalculation'}
        )
        for src, dst in transitions.items():
            if src.name == 'in_basket_normal':
                self.assertEqual(dst.name, 'in_recalculation')
            if src.name == 'in_recalculation':
                self.assertEqual(dst.name, 'in_basket_normal')

        transitions = statechart['do_goto_in_basket_freeze']
        self.assertTrue(len(transitions) == 2)
        self.assertSetEqual(
            {x.name for x in transitions},
            {'in_basket_freeze', 'in_recalculation'}
        )
        for src, dst in transitions.items():
            if src.name == 'in_basket_freeze':
                self.assertEqual(dst.name, 'in_recalculation')
            if src.name == 'in_recalculation':
                self.assertEqual(dst.name, 'in_basket_freeze')

        transitions = statechart['do_add_to_basket']
        self.assertTrue(len(transitions) == 3)
        self.assertSetEqual(
            {x.name for x in transitions},
            {'in_basket_normal', 'in_basket_freeze', 'in_basket_empty'}
        )
        for src, dst in transitions.items():
            if src.name == 'in_basket_normal':
                self.assertEqual(dst.name, 'in_recalculation')
            if src.name == 'in_basket_freeze':
                self.assertEqual(dst.name, 'in_recalculation')
            if src.name == 'in_basket_empty':
                self.assertEqual(dst.name, 'in_recalculation')

        transitions = statechart['do_remove_product']
        self.assertTrue(len(transitions) == 2)
        self.assertSetEqual(
            {x.name for x in transitions},
            {'in_basket_normal', 'in_basket_freeze'}
        )
        if src.name == 'in_basket_normal':
            self.assertEqual(dst.name, 'in_recalculation')
        if src.name == 'in_basket_freeze':
            self.assertEqual(dst.name, 'in_recalculation')

    def test_callbacks(self):
        path = get_xml_path()
        with open(path) as xml:
            parser = HSMEXMLParser(xml)
            table = parser.parse()

        all_states = set()
        for mapping in table._statechart.values():
            for s1, s2 in mapping.items():
                all_states.add(s1)
                all_states.add(s2)

        in_recalculation_state = [
            s for s in all_states
            if s.name == 'in_recalculation'
        ][0]
        self.assertDictEqual(
            in_recalculation_state.callbacks, {
                'on_exit': 'tests.charts.basket_callbacks.on_exit_in_recalculation',
                'on_change': 'tests.charts.basket_callbacks.on_change_in_recalculation',
                'on_enter': 'tests.charts.basket_callbacks.on_enter_in_recalculation',
            }
        )
        in_basket_normal = [
            s for s in all_states
            if s.name == 'in_basket_normal'
        ][0]
        self.assertDictEqual(
            in_basket_normal.callbacks, {
                'on_change': 'tests.charts.basket_callbacks.on_change_in_basket_normal'
            }
        )
        in_basket_freeze = [
            s for s in all_states
            if s.name == 'in_basket_freeze'
        ][0]
        self.assertDictEqual(
            in_basket_freeze.callbacks, {
                'on_enter': 'tests.charts.basket_callbacks.on_enter_in_basket_freeze'
            }
        )
        in_basket_empty = [
            s for s in all_states
            if s.name == 'in_basket_empty'
        ][0]
        self.assertFalse(in_basket_empty.callbacks)
