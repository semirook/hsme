# coding: utf-8
import unittest

from fsm.parsers import (
    HSMEDictsParser,
    HSMEParserError,
    HSMEStateChart,
)
from .charts.rules import (
    BROKEN_RULES_CHART,
    NO_INITIAL_RULES_CHART,
    RULES_CHART,
    SIMPLE_RULES_CHART,
    TWO_INITIAL_RULES_CHART,
)


class TestHSMEDictParser(unittest.TestCase):

    def test_real_chart(self):
        parser = HSMEDictsParser(RULES_CHART)
        model = parser.parse()
        self.assertTrue(isinstance(model, parser.STATE_CHART_CLS))
        self.assertTrue(isinstance(model.initial_state, parser.STATE_CLS))
        self.assertFalse(model.current_state)
        for state in model.final_states:
            self.assertTrue(isinstance(state, parser.STATE_CLS))

        self.assertTrue(model.initial_state.name == 'one')
        self.assertListEqual(
            [m.name for m in model.final_states],
            ['four', 'five', 'six']
        )

    def test_no_initial_chart(self):
        parser = HSMEDictsParser(NO_INITIAL_RULES_CHART)
        with self.assertRaises(HSMEParserError):
            parser.parse()

    def test_multiple_initials_chart(self):
        parser = HSMEDictsParser(TWO_INITIAL_RULES_CHART)
        with self.assertRaises(HSMEParserError):
            parser.parse()

    def test_broken_chart(self):
        parser = HSMEDictsParser(BROKEN_RULES_CHART)
        with self.assertRaises(HSMEParserError):
            parser.parse()

    def test_invalid_chart(self):
        with self.assertRaises(HSMEParserError):
            HSMEDictsParser(42)


class TestHSMEChartSerialization(unittest.TestCase):

    def test_serialization(self):
        parser = HSMEDictsParser(SIMPLE_RULES_CHART)
        model = parser.parse()
        reference_struct = {
            'chart_id': 'dcf55c31ae9355a66319061aa4f23449',
            'current_state': None,
            'final_states': [
                {
                    'action': None,
                    'events': [],
                    'is_final': True,
                    'is_initial': False,
                    'name': 'two',
                    'trigger': None
                },
                {
                    'action': None,
                    'events': [],
                    'is_final': True,
                    'is_initial': False,
                    'name': 'three',
                    'trigger': None
                }
            ],
            'history': [],
            'initial_state': {
                'action': None,
                'events': [(True, 'two'), (False, 'three')],
                'is_final': False,
                'is_initial': True,
                'name': 'one',
                'trigger': None
            },
            'statechart': [
                (True, (
                    {
                        'action': None,
                        'events': [(True, 'two'), (False, 'three')],
                        'is_final': False,
                        'is_initial': True,
                        'name': 'one',
                        'trigger': None
                    },
                    {
                        'action': None,
                        'events': [],
                        'is_final': True,
                        'is_initial': False,
                        'name': 'two',
                        'trigger': None
                    }
                )),
                (False, (
                    {
                        'action': None,
                        'events': [(True, 'two'), (False, 'three')],
                        'is_final': False,
                        'is_initial': True,
                        'name': 'one',
                        'trigger': None
                    },
                    {
                        'action': None,
                        'events': [],
                        'is_final': True,
                        'is_initial': False,
                        'name': 'three',
                        'trigger': None
                    }
                ))
            ]
        }
        self.assertDictEqual(model.as_dict(), reference_struct)

    def test_deserialization(self):
        parser_1 = HSMEDictsParser(SIMPLE_RULES_CHART)
        model_1 = parser_1.parse()
        internal_struct = model_1.as_dict()

        parser_2 = HSMEDictsParser(SIMPLE_RULES_CHART)
        model_2 = parser_2.parse()

        self.assertTrue(HSMEStateChart.as_obj(internal_struct) == model_2)
