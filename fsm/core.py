# coding: utf-8
import json
import time
import calendar
from collections import namedtuple

from fsm.parsers import HSMEStateChart, HSMEDictsParser


class HSMERunnerError(Exception):
    pass


class HSMEWrongEventError(Exception):
    pass


class HSMEWrongTriggerError(HSMEWrongEventError):
    pass


class HSMEUndefinedTriggerError(Exception):
    pass


class HSMEUndefinedActionError(Exception):
    pass


HSMEProxyObject = namedtuple(
    'HSMEProxyObject', [
        'fsm',
        'event',
        'payload',
        'src',
        'dst',
    ]
)


class HSMERunner(object):

    STATE_CHART_CLS = HSMEStateChart
    STATE_CHART_PARSER = HSMEDictsParser

    def __init__(
        self,
        trigger_source=None,
        action_source=None,
    ):
        self.model = None
        self.trigger_source = trigger_source
        self.action_source = action_source

    def __getattribute__(self, name):
        if name in set([
            'datamodel',
            'history',
            'in_state',
            'is_finished',
            'save',
            'start',
        ]) and not self.is_loaded():
            raise HSMERunnerError('Load machine first')

        return object.__getattribute__(self, name)

    def __repr__(self):
        if self.is_loaded():
            return 'HSMERunner: {0}'.format(self.model.chart_id)
        else:
            return 'HSMERunner: empty'

    def load(self, model=None, deserializer=None):
        self.model = None

        if not isinstance(model, self.STATE_CHART_CLS):
            deserializer = deserializer or json.loads
            model = deserializer(model)
            model = self.STATE_CHART_CLS.as_obj(model)

        if not isinstance(model, self.STATE_CHART_CLS):
            raise HSMERunnerError(
                'Invalid statechart format, '
                'HSMEStateChart instance expected'
            )

        self.model = model

        return self

    def dump(self, serializer=None):
        if not self.is_loaded():
            raise HSMERunnerError('Load and start machine first')

        serializer = serializer or json.dumps
        return serializer(self.model.as_dict())

    def parse(self, chart):
        model = self.STATE_CHART_PARSER(chart).parse()
        return self.load(model)

    def is_loaded(self):
        return self.model is not None

    def is_started(self):
        return self.current_state is not None

    def start(self, payload=None):
        if self.is_started():
            return False

        src = self.model.current_state
        dst = self.model.initial_state
        hsme_proxy = HSMEProxyObject(
            fsm=self,
            event=None,
            src=src,
            dst=dst,
            payload=payload,
        )
        return self._do_transition(hsme_proxy)

    def send(self, event_name, payload=None):
        if not self.is_loaded() or not self.is_started():
            raise HSMERunnerError('Load and start machine first')

        src = self.current_state
        if event_name not in self.model.statechart:
            raise HSMEWrongEventError(
                'Event {0} is unregistered'.format(
                    repr(event_name)
                )
            )
        if not self.can_send(event_name):
            raise HSMEWrongEventError(
                'Event {0} is inappropriate in current state {1}'.format(
                    repr(event_name), src.name
                )
            )
        event_transition = self.model.statechart[event_name]
        dst = src in event_transition and event_transition[src]
        hsme_proxy = HSMEProxyObject(
            fsm=self,
            event=event_name,
            payload=payload,
            src=src,
            dst=dst,
        )
        return self._do_transition(hsme_proxy)

    def can_send(self, event_name):
        if not self.is_loaded():
            raise HSMERunnerError('Load machine first')

        if event_name not in self.model.statechart:
            return False

        event_transition = self.model.statechart[event_name]

        return self.current_state in event_transition

    def get_possible_transitions(self):
        if self.is_loaded() and self.is_started():
            return self.current_state.events
        else:
            raise HSMERunnerError('Load and start machine first')

    def in_state(self, state_name):
        if self.is_loaded() and self.is_started():
            return self.current_state.name == state_name
        else:
            raise HSMERunnerError('Load and start machine first')

    def is_finished(self):
        if self.is_loaded() and self.is_started():
            return (
                bool(self.model.final_states) and
                self.current_state in self.model.final_states
            )
        else:
            raise HSMERunnerError('Load and start machine first')

    @property
    def current_state(self):
        return self.model.current_state if self.model else None

    @property
    def history(self):
        if self.model.history:
            chain = ' -> '.join(
                '({0}:{1} @{2})'.format(h['state'], h['event'], h['timestamp'])
                for h in self.model.history
            )
            return '{0} => {1}'.format(repr(self.model), chain)
        else:
            return '{0} => not started'.format(repr(self.model))

    def _do_transition(self, hsme_proxy):
        dst = hsme_proxy.dst
        if not dst:
            return False

        self.model.current_state = dst

        self.model.history.append({
            'state': dst.name,
            'event': hsme_proxy.event,
            'timestamp': calendar.timegm(time.gmtime()),
        })

        if dst.action and self.action_source:
            action = self.action_source(hsme_proxy, dst.action)
            if not action:
                raise HSMEUndefinedActionError(
                    'Action source {0} is registered for the state {1} '
                    'but not found'.format(
                        repr(dst.action),
                        repr(dst.name)
                    )
                )
            action(hsme_proxy)

        if dst.trigger and self.trigger_source:
            trigger = self.trigger_source(hsme_proxy, dst.trigger)
            if not trigger:
                raise HSMEUndefinedTriggerError(
                    'Trigger source {0} is registered for the state {1} '
                    'but not found'.format(
                        repr(dst.trigger),
                        repr(dst.name)
                    )
                )
            trigger_event = trigger(hsme_proxy)
            if not self.can_send(trigger_event):
                raise HSMEWrongTriggerError(
                    'Event {0} produced by the trigger {1} '
                    'is inappropriate in current state {2}'.format(
                        repr(trigger_event),
                        repr(trigger),
                        repr(self.model.current_state),
                    )
                )

            return self.send(trigger_event, hsme_proxy.payload)

        return True
