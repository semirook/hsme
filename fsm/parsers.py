# coding: utf-8
import os
import io
import sys
import types
import hashlib
import xml.etree.ElementTree as ET


PY = sys.version_info
PY3K = PY >= (3, 0, 0)


class HSMEParserError(Exception):
    pass


class HSMEState(object):

    def __init__(
        self,
        name,
        events=None,
        trigger=None,
        action=None,
        is_initial=False,
        is_final=False
    ):
        self.name = name
        self.trigger = trigger
        self.action = action
        self.events = events or {}
        self.is_initial = is_initial
        self.is_final = is_final
        if not self.events:
            self.is_final = True

    def __repr__(self):
        return 'HSMEState: {0}'.format(self.name)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return (
            isinstance(other, HSMEState)
            and self.name == other.name
            and self.events == other.events
            and self.is_initial == other.is_initial
            and self.is_final == other.is_final
        )

    @classmethod
    def as_obj(cls, raw_dict):
        return cls(
            name=raw_dict['name'],
            events={e: s for e, s in raw_dict['events']},
            trigger=raw_dict['trigger'],
            action=raw_dict['action'],
            is_initial=raw_dict['is_initial'],
            is_final=raw_dict['is_final'],
        )

    def as_dict(self):
        return {
            'name': self.name,
            'events': [(e, s) for e, s in self.events.items()],
            'trigger': self.trigger,
            'action': self.action,
            'is_initial': self.is_initial,
            'is_final': self.is_final,
        }


class HSMEStateChart(object):

    STATE_CLS = HSMEState

    def __init__(
        self,
        chart_id=None,
        current_state=None,
        initial_state=None,
        final_states=None,
        history=None,
        statechart=None
    ):
        self.chart_id = chart_id
        self.current_state = current_state
        self.initial_state = initial_state
        self.final_states = final_states or []
        self.history = history or []
        self.statechart = statechart or {}

    def __repr__(self):
        return 'HSMEStateChart: {0}'.format(self.chart_id)

    def __eq__(self, other):
        return (
            isinstance(other, HSMEStateChart)
            and self.chart_id == other.chart_id
            and self.initial_state == other.initial_state
            and self.final_states == other.final_states
            and self.statechart == other.statechart
        )

    @classmethod
    def as_obj(cls, raw_dict):
        statechart = {}
        for event, states_pair in raw_dict['statechart']:
            src, dst = states_pair
            statechart.setdefault(event, {}).update({
                cls.STATE_CLS.as_obj(src): cls.STATE_CLS.as_obj(dst)
            })

        return cls(
            chart_id=raw_dict['chart_id'],
            current_state=(
                cls.STATE_CLS.as_obj(raw_dict['current_state'])
                if raw_dict['current_state']
                else None
            ),
            initial_state=cls.STATE_CLS.as_obj(raw_dict['initial_state']),
            final_states=[
                cls.STATE_CLS.as_obj(i)
                for i in raw_dict['final_states']
            ],
            history=raw_dict['history'],
            statechart=statechart,
        )

    def as_dict(self):
        statechart = []
        for event, states_map in self.statechart.items():
            for src, dst in states_map.items():
                statechart.append((event, (src.as_dict(), dst.as_dict())))

        return {
            'chart_id': self.chart_id,
            'current_state': (
                self.current_state.as_dict()
                if self.current_state else None
            ),
            'initial_state': self.initial_state.as_dict(),
            'final_states': [i.as_dict() for i in self.final_states],
            'statechart': statechart,
            'history': self.history,
        }


class HSMEDictsParser(object):

    STATE_CLS = HSMEState
    STATE_CHART_CLS = HSMEStateChart

    def __init__(self, chart=None):
        self.chart = chart or []

    def get_chart_id(self, obj):
        return hashlib.md5(repr(obj).encode('utf8')).hexdigest()

    def parse(self):
        states_map = {}
        initial_state = None
        for state in self.chart:
            state_id = state['state']
            state_inst = self.STATE_CLS(
                name=state_id,
                events=state.get('events'),
                trigger=state.get('trigger'),
                action=state.get('action'),
                is_initial=state.get('is_initial', False),
            )
            states_map[state_id] = state_inst
            if state_inst.is_initial:
                initial_state = state_inst

        events_map = {}
        final_states = []
        for state_inst in states_map.values():
            for e, dst in state_inst.events.items():
                events_map.setdefault(e, {}).update({
                    state_inst: states_map[dst]
                })
            if state_inst.is_final:
                final_states.append(state_inst)

        model = self.STATE_CHART_CLS(
            chart_id=self.get_chart_id(events_map),
            initial_state=initial_state,
            final_states=final_states,
            statechart=events_map,
        )

        return model
