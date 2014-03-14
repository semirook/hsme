# coding=utf-8
import types
import hashlib
from xml.etree.ElementTree import parse


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


class HSMEStateChart(object):

    def __init__(self):
        self._id = None
        self._current_state = None
        self._init_state = None
        self._final_state = None
        self._statechart = {}
        self._datamodel = {}
        self._history = []

    def __repr__(self):
        return '<HSMEStateChart: %s>' % self._id


class HSMEParserBase(object):

    def __init__(self, doc, doc_id=None, datamodel=None):
        self.doc = doc
        self.doc_id = doc_id or self.get_doc_id()
        self.datamodel = datamodel or {}
        self.table = HSMEStateChart()

    def get_doc_id(self):
        return hashlib.md5(repr(self.doc)).hexdigest()

    def _compose(self, events_map, states_map):
        for state_inst in states_map.itervalues():
            for e, dst in state_inst.events.iteritems():
                events_map.setdefault(e, {}).update({
                    state_inst: states_map[dst]
                })

        self.table._id = self.doc_id
        self.table._statechart = events_map
        self.table._datamodel.update(self.datamodel)


class HSMEDictsParser(HSMEParserBase):

    def parse(self):
        events = {}
        states = {}

        for state in self.doc:
            state_id = state['id']
            state_inst = HSMEState(
                state['id'],
                state.get('events'),
                state.get('callbacks'),
                state.get('initial', False),
                state.get('final', False)
            )
            states[state_id] = state_inst

            if state_inst.is_initial:
                self.table._init_state = state_inst
            if state_inst.is_final:
                self.table._final_state = state_inst

        self._compose(events, states)

        return self.table


class HSMEXMLParser(HSMEParserBase):

    def __init__(self, doc, doc_id=None, datamodel=None):
        super(HSMEXMLParser, self).__init__(doc, doc_id, datamodel)
        if isinstance(doc, basestring):
            self.doc = open(doc, 'rb')

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

    def _parse(self):
        states = {}
        events = {}
        doc = parse(self.doc)

        for state, is_meta in self._parse_state(doc):
            state_id = state.attrib['id']
            events_map = {k: v for k, v in self._parse_transition(state)}
            if is_meta:
                events_map.update({
                    k: v for k, v in self._make_events_for_meta(state)
                })
            state_inst = HSMEState(
                state_id,
                events=events_map,
                callbacks=self._parse_callbacks(state),
                is_initial='initial' in state.attrib,
                is_final='final' in state.attrib,
            )
            states[state_id] = state_inst

            if state_inst.is_initial:
                self.table._init_state = state_inst
            if state_inst.is_final:
                self.table._final_state = state_inst

        self._compose(events, states)

        return self.table

    def parse(self):
        try:
            return self._parse()
        except Exception as e:
            raise e
        finally:
            if isinstance(self.doc, types.FileType):
                self.doc.close()
