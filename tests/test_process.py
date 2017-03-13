# coding: utf-8
import unittest
import sqlite3

from fsm.core import (
    HSMERunner,
    HSMERunnerError,
    HSMEWrongTriggerError,
)
from .charts.rules import (
    RULES_CHART,
    SIMPLE_RULES_CHART,
    MULTIPLE_TRIGGERS_RULES_CHART,
)


def insert_payload_action(proxy):
    payload = proxy.payload
    db = payload['db']
    cur = db.cursor()
    cur.execute(
        'insert into people values (?, ?)',
        ('anon', payload['user_id'])
    )
    db.commit()
    cur.close()


def event_trigger_source(proxy, trigger_id):
    trigger = TRIGGERS_MAP.get(trigger_id)
    return trigger(proxy)


def multiple_event_trigger_source(proxy, trigger_ids):
    event = False
    for trigger_id in trigger_ids:
        event_producer = TRIGGERS_MAP.get(trigger_id)
        event = event_producer(proxy)
        if not event:
            continue
        else:
            return event

    return event


def state_action_source(proxy, action_id):
    action = ACTIONS_MAP.get(action_id)
    return action(proxy)


TRIGGERS_MAP = {
    1: lambda proxy: True,
    2: lambda proxy: False,
    3: lambda proxy: True,
}


ACTIONS_MAP = {
    1: lambda proxy: proxy,
    2: insert_payload_action,
    3: insert_payload_action,
}


class TestHSMERunner(unittest.TestCase):

    def test_load_start_flow(self):
        hsme = HSMERunner()
        self.assertFalse(hsme.is_loaded())

        with self.assertRaises(HSMERunnerError):
            hsme.dump()
        with self.assertRaises(HSMERunnerError):
            hsme.start()
        with self.assertRaises(HSMERunnerError):
            hsme.send(False)
        with self.assertRaises(HSMERunnerError):
            hsme.can_send(False)
        with self.assertRaises(HSMERunnerError):
            hsme.get_possible_transitions()
        with self.assertRaises(HSMERunnerError):
            hsme.in_state('one')

        hsme.parse(RULES_CHART)

        self.assertTrue(hsme.is_loaded())
        self.assertFalse(hsme.is_started())
        self.assertTrue(hsme.current_state is None)

        with self.assertRaises(HSMERunnerError):
            hsme.in_state('one')

        with self.assertRaises(HSMERunnerError):
            hsme.send(False)

        hsme.start()
        self.assertTrue(hsme.is_started())
        self.assertTrue(hsme.in_state('one'))

    def test_transition_flow(self):
        hsme = HSMERunner()
        hsme.parse(RULES_CHART)
        hsme.start()

        self.assertTrue(hsme.in_state('one'))
        self.assertDictEqual(
            hsme.get_possible_transitions(),
            {True: 'two', False: 'three'},
        )
        self.assertTrue(hsme.can_send(True))
        self.assertTrue(hsme.can_send(False))
        self.assertFalse(hsme.can_send('invalid_event'))

        hsme.send(True)
        self.assertTrue(hsme.in_state('two'))

    def test_runner_reload(self):
        hsme = HSMERunner()
        hsme.parse(RULES_CHART)
        model_1 = hsme.model

        hsme.parse(SIMPLE_RULES_CHART)
        model_2 = hsme.model

        self.assertTrue(model_1 != model_2)

    def test_dump_load_flow(self):
        hsme = HSMERunner()
        hsme.parse(RULES_CHART)
        serialized_hsme = hsme.dump()

        hsme_2 = HSMERunner()
        hsme_2.load(serialized_hsme)

        self.assertTrue(hsme.model == hsme_2.model)

        hsme.start()
        hsme.send(False)
        self.assertTrue(hsme.in_state('three'))

        serialized_hsme_step = hsme.dump()
        hsme_2.load(serialized_hsme_step)

        self.assertTrue(hsme_2.in_state('three'))

    def test_triggers_flow(self):
        hsme = HSMERunner(trigger_source=event_trigger_source)
        hsme.parse(RULES_CHART)
        hsme.start()

        self.assertTrue(hsme.in_state('five'))

        should_be_history = [
            {'state': 'one', 'event': None},
            {'state': 'two', 'event': True},
            {'state': 'five', 'event': False},
        ]
        for i, rec in enumerate(hsme.model.history):
            self.assertTrue(rec['state'] == should_be_history[i]['state'])
            self.assertTrue(rec['event'] == should_be_history[i]['event'])

    def test_wrong_triggers_flow(self):
        hsme = HSMERunner(trigger_source=lambda proxy, i: 'wrong_event')
        hsme.parse(RULES_CHART)

        with self.assertRaises(HSMEWrongTriggerError):
            hsme.start()

    def test_multiple_triggers_flow(self):
        hsme = HSMERunner(
            trigger_source=multiple_event_trigger_source,
        )
        hsme.parse(MULTIPLE_TRIGGERS_RULES_CHART)
        hsme.start()

        self.assertTrue(hsme.in_state('three'))

        should_be_history = [
            {'state': 'one', 'event': None},
            {'state': 'three', 'event': True},
        ]
        for i, rec in enumerate(hsme.model.history):
            self.assertTrue(rec['state'] == should_be_history[i]['state'])
            self.assertTrue(rec['event'] == should_be_history[i]['event'])

    def test_actions_flow(self):
        hsme = HSMERunner(
            trigger_source=event_trigger_source,
            action_source=state_action_source,
        )
        db = sqlite3.connect(':memory:')
        db.execute('create table people (name, age)')

        payload = {'user_id': 42, 'db': db}

        hsme.parse(RULES_CHART)
        hsme.start(payload)
        self.assertTrue(hsme.in_state('five'))

        cur = db.cursor()
        cur.execute('select * from people where name=:who', {'who': 'anon'})
        action_result = cur.fetchall()
        cur.close()
        db.close()

        self.assertListEqual(action_result, [('anon', 42)])
