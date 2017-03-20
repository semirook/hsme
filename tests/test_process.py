# coding: utf-8
import pytest
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


class TestHSMERunner(object):

    def test_load_start_flow(self):
        hsme = HSMERunner()
        assert not hsme.is_loaded()

        with pytest.raises(HSMERunnerError):
            hsme.dump()
        with pytest.raises(HSMERunnerError):
            hsme.start()
        with pytest.raises(HSMERunnerError):
            hsme.send(False)
        with pytest.raises(HSMERunnerError):
            hsme.can_send(False)
        with pytest.raises(HSMERunnerError):
            hsme.get_possible_transitions()
        with pytest.raises(HSMERunnerError):
            hsme.in_state('one')

        hsme.parse(RULES_CHART)

        assert hsme.is_loaded()
        assert not hsme.is_started()
        assert hsme.current_state is None

        with pytest.raises(HSMERunnerError):
            hsme.in_state('one')

        with pytest.raises(HSMERunnerError):
            hsme.send(False)

        hsme.start()
        assert hsme.is_started()
        assert hsme.in_state('one')

    def test_transition_flow(self):
        hsme = HSMERunner()
        hsme.parse(RULES_CHART)
        hsme.start()

        assert hsme.in_state('one')
        assert hsme.get_possible_transitions() == {True: 'two', False: 'three'}
        assert hsme.can_send(True)
        assert hsme.can_send(False)
        assert not hsme.can_send('invalid_event')

        hsme.send(True)
        assert hsme.in_state('two')

    def test_runner_reload(self):
        hsme = HSMERunner()
        hsme.parse(RULES_CHART)
        model_1 = hsme.model

        hsme.parse(SIMPLE_RULES_CHART)
        model_2 = hsme.model

        assert model_1 != model_2

    def test_dump_load_flow(self):
        hsme = HSMERunner()
        hsme.parse(RULES_CHART)
        serialized_hsme = hsme.dump()

        hsme_2 = HSMERunner()
        hsme_2.load(serialized_hsme)

        assert hsme.model == hsme_2.model

        hsme.start()
        hsme.send(False)
        assert hsme.in_state('three')

        serialized_hsme_step = hsme.dump()
        hsme_2.load(serialized_hsme_step)

        assert hsme_2.in_state('three')

    def test_triggers_flow(self):
        hsme = HSMERunner(trigger_source=event_trigger_source)
        hsme.parse(RULES_CHART)
        hsme.start()

        assert hsme.in_state('five')

        should_be_history = [
            {'state': 'one', 'event': None},
            {'state': 'two', 'event': True},
            {'state': 'five', 'event': False},
        ]
        for i, rec in enumerate(hsme.model.history):
            assert rec['state'] == should_be_history[i]['state']
            assert rec['event'] == should_be_history[i]['event']

    def test_wrong_triggers_flow(self):
        hsme = HSMERunner(trigger_source=lambda proxy, i: 'wrong_event')
        hsme.parse(RULES_CHART)

        with pytest.raises(HSMEWrongTriggerError):
            hsme.start()

    def test_multiple_triggers_flow(self):
        hsme = HSMERunner(
            trigger_source=multiple_event_trigger_source,
        )
        hsme.parse(MULTIPLE_TRIGGERS_RULES_CHART)
        hsme.start()

        assert hsme.in_state('three')

        should_be_history = [
            {'state': 'one', 'event': None},
            {'state': 'three', 'event': True},
        ]
        for i, rec in enumerate(hsme.model.history):
            assert rec['state'] == should_be_history[i]['state']
            assert rec['event'] == should_be_history[i]['event']

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
        assert hsme.in_state('five')

        cur = db.cursor()
        cur.execute('select * from people where name=:who', {'who': 'anon'})
        action_result = cur.fetchall()
        cur.close()
        db.close()

        assert action_result, [('anon', 42)]
