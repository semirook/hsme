# coding: utf-8
import os
from unittest import TestCase
from fsm.parsers import HSMEXMLParser, HSMEDictsParser
from .charts.basket import BASKET_CHART


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


class TestParsersEquality(TestCase):

    def test_dict_and_xml(self):
        path = get_xml_path()
        table_from_xml = HSMEXMLParser(path, doc_id='basket').parse()
        table_from_dict = HSMEDictsParser(BASKET_CHART, doc_id='basket').parse()

        self.assertEqual(table_from_xml._id, table_from_dict._id)
        self.assertEqual(table_from_xml._init_state, table_from_dict._init_state)
        self.assertEqual(table_from_xml._final_state, table_from_dict._final_state)

        self.assertTrue(sorted(table_from_dict._statechart) == sorted(table_from_xml._statechart))
        sorted_events = sorted(table_from_dict._statechart)

        for event in sorted_events:
            dict_trans_map = table_from_dict._statechart[event]
            xml_trans_map = table_from_xml._statechart[event]

            dict_src_names = sorted(x.name for x in dict_trans_map.keys())
            xml_src_names = sorted(x.name for x in xml_trans_map.keys())
            self.assertListEqual(dict_src_names, xml_src_names)

            dict_dst_names = sorted(x.name for x in dict_trans_map.values())
            xml_dst_names = sorted(x.name for x in xml_trans_map.values())
            self.assertListEqual(dict_dst_names, xml_dst_names)

            xml_src_events = sorted(x.events for x in xml_trans_map.keys())
            dict_src_events = sorted(x.events for x in dict_trans_map.keys())
            self.assertListEqual(dict_src_events, xml_src_events)

            xml_dst_events = sorted(x.events for x in xml_trans_map.values())
            dict_dst_events = sorted(x.events for x in dict_trans_map.values())
            self.assertListEqual(dict_dst_events, xml_dst_events)

        for event in sorted_events:
            dict_trans_map = table_from_dict._statechart[event]
            xml_trans_map = table_from_xml._statechart[event]

            dict_src_states = sorted(dict_trans_map.keys())
            xml_src_states = sorted(xml_trans_map.keys())
            self.assertListEqual(dict_src_states, xml_src_states)
            self.assertListEqual(
                [x.events for x in dict_src_states],
                [x.events for x in xml_src_states]
            )

            dict_dst_states = sorted(dict_trans_map.values())
            xml_dst_states = sorted(xml_trans_map.values())
            self.assertListEqual(dict_dst_states, xml_dst_states)
            self.assertListEqual(
                [x.events for x in dict_dst_states],
                [x.events for x in xml_dst_states]
            )
