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
        callbacks=None,
        is_initial=False,
        is_final=False
    ):
        self.name = name
        self.events = events or {}
        self.callbacks = callbacks or {}
        self.is_initial = is_initial
        self.is_final = is_final

    def __repr__(self):
        return '<HSMEState: %s>' % self.name

    def __hash__(self):
        return hash(self.name)

    def __lt__(self, other):
         return self.name < other.name

    def __eq__(self, other):
        return (
            isinstance(other, HSMEState)
            and self.name == other.name
            and self.events == other.events
            and self.is_initial == other.is_initial
            and self.is_final == other.is_final
        )


class HSMEStateChart(object):

    def __init__(self):
        self._id = None
        self._current_state = None
        self._init_state = None
        self._final_state = None
        self._statechart = {}
        self._datamodel = {}

    def __repr__(self):
        return '<HSMEStateChart: %s>' % self._id


class HSMEParserBase(object):

    STATE_CLS = HSMEState
    STATE_CHART_CLS = HSMEStateChart

    def __init__(self, chart=None):
        self.chart = chart
        self.model = self.STATE_CHART_CLS()

    @property
    def model_id(self):
        return hashlib.md5(repr(self.model).encode('utf8')).hexdigest()

    def _compose(self, states_map):
        events_map = {}
        for state_inst in states_map.values():
            for e, dst in state_inst.events.items():
                events_map.setdefault(e, {}).update({
                    state_inst: states_map[dst]
                })

        self.model._id = self.model_id
        self.model._statechart = events_map

        return self.model


class HSMEDictsParser(HSMEParserBase):

    def parse(self):
        states = {}

        for state in self.chart:
            state_id = state['id']
            state_inst = self.STATE_CLS(
                state['id'],
                state.get('events'),
                state.get('callbacks'),
                state.get('initial', False),
                state.get('final', False)
            )
            states[state_id] = state_inst

            if state_inst.is_initial:
                self.model._init_state = state_inst
            if state_inst.is_final:
                self.model._final_state = state_inst

        self._compose(states)

        return self.model


class HSMEXMLParser(HSMEParserBase):

    def _parse_state(self, elem, is_meta=True):
        for state in elem.iterfind('state'):
            yield state, is_meta
            for sub in self._parse_state(state, False):
                yield sub

    def _parse_transition(self, elem):
        for trans in elem.iterfind('transition'):
            yield (trans.attrib['event'], trans.attrib['next'])

    def _make_events_for_meta(self, elem):
        for state in elem.iterfind('state'):
            event_name = 'do_goto_%s' % state.attrib['id']
            next_name = state.attrib['id']
            yield (event_name, next_name)

    def _parse_callbacks(self, elem):
        targetns = elem.attrib['targetns'] if 'targetns' in elem.attrib else ''
        joiner = '.' if targetns else ''
        concat = lambda attr: joiner.join([targetns, attr])
        callbacks = {}

        on_enter = elem.find('onentry')
        if on_enter is not None:
            callbacks['on_enter'] = concat(on_enter.attrib['target'])

        on_change = elem.find('onchange')
        if on_change is not None:
            callbacks['on_change'] = concat(on_change.attrib['target'])

        on_exit = elem.find('onexit')
        if on_exit is not None:
            callbacks['on_exit'] = concat(on_exit.attrib['target'])

        return callbacks

    def parse(self):
        states = {}
        doc = ET.fromstring(self.chart)

        for state, is_meta in self._parse_state(doc):
            state_id = state.attrib['id']
            events_map = dict((k, v) for k, v in self._parse_transition(state))
            if is_meta:
                events_map.update(
                    dict((k, v) for k, v in self._make_events_for_meta(state))
                )
            state_inst = self.STATE_CLS(
                state_id,
                events=events_map,
                callbacks=self._parse_callbacks(state),
                is_initial='initial' in state.attrib,
                is_final='final' in state.attrib,
            )
            states[state_id] = state_inst

            if state_inst.is_initial:
                self.model._init_state = state_inst
            if state_inst.is_final:
                self.model._final_state = state_inst

        self._compose(states)

        return self.model

    @classmethod
    def parse_from_path(cls, chart):
        if not os.path.exists(chart):
            raise HSMEParserError('File "%s" does not exist' % chart)

        with open(chart, 'rb') as chart_file:
            parser = cls(chart_file.read())
            try:
                return parser.parse()
            except Exception as e:
                raise e

    @classmethod
    def parse_from_file(cls, chart):
        if not isinstance(chart, io.IOBase if PY3K else types.FileType):
            raise HSMEParserError('The chart is not a file instance')

        parser = cls(chart=chart.read())
        try:
            return parser.parse()
        except Exception as e:
            raise e
        finally:
            chart.close()

    @classmethod
    def parse_from_string(cls, chart):
        if not isinstance(chart, str if PY3K else types.StringTypes):
            raise HSMEParserError('The chart is not a string')

        parser = cls(chart=chart)
        try:
            return parser.parse()
        except Exception as e:
            raise e
