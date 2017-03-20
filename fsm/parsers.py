# coding: utf-8
import hashlib
import collections


class HSMEParserError(Exception):
    """Raised by the transition map parser if some kind of ambiguity
    has happened or invalid map format was used. Like multiple initial states
    declarations (FSM can have only one entry point) or no state id/name
    was found.
    """


class HSMEState(object):
    """Internal state representation object with state-related data,
    serialization/deserialization methods (:meth:`as_obj` and :meth:`as_dict`)
    and comparison logic.
    """
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
            isinstance(other, self.__class__) and
            self.name == other.name and
            self.events == other.events and
            self.is_initial == other.is_initial and
            self.is_final == other.is_final
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
    """Internal FSM transition map representation. Consists of efficient
    ``statechart`` structure, ``current_state``, ``initial_state``
    and ``final_states`` containers, widely used in the Runner. Also, contains
    serialization/deserialization methods (:meth:`as_obj` and :meth:`as_dict`)

    :param chart_id: some id to mark FSM model.
    :param current_state: ``HSMEState`` instance of the active transition state.
    :param initial_state: ``HSMEState`` instance of the FSM root state.
    :param final_states: a list of ``HSMEState`` instances with FSM edges.
    :param history: a list of dicts like ``{'state': 'name', 'event': 'name'}``.
    :param statechart: transition dict structure with event-to-states mapping
        ``{'event': {HSMEState: HSMEState}}``
    """

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
            isinstance(other, self.__class__) and
            self.chart_id == other.chart_id and
            self.initial_state == other.initial_state and
            self.final_states == other.final_states and
            self.statechart == other.statechart
        )

    @classmethod
    def as_obj(cls, raw_dict):
        """The ``HSMEStateChart`` factory.

        :param raw_dict: dict structure produced by the :meth:`as_dict` method.
        :returns: ``HSMEStateChart`` instance.
        """
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
        """Transition map serialization method. Returns a dict with full
        explicit structure::

            {
                'chart_id': 'dcf55c31ae9355a66319061aa4f23449',
                'current_state': None,
                'initial_state': {
                    'name': 'one',
                    'events': [
                        (True, 'two'),
                        (False, 'three')
                    ],
                    'trigger': None,
                    'action': None,
                    'is_initial': True,
                    'is_final': False
                },
                'statechart': [
                    (True, ({
                        'name': 'one',
                        'events': [(True, 'two'), (False, 'three')],
                        'trigger': None,
                        'action': None,
                        'is_initial': True,
                        'is_final': False
                    }, ... ))
                ],
                'history': [],
                'final_states': [...]
            }
        """
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
    """Standard FSM parser, ``HSMEStateChart`` fabric. Parses special raw
    structure like::

        RULES_CHART = [
            {
                'state': 'one',
                'is_initial': True,
                'trigger': 1,
                'events': {
                    True: 'two',
                    False: 'three',
                },
            },
            {
                'state': 'two',
                'trigger': 2,
                'events': {
                    True: 'four',
                    False: 'five',
                },
            },
            {
                'state': 'three',
                'trigger': 3,
                'events': {
                    True: 'six',
                    False: 'six',
                },
            },
            {
                'state': 'four',
                'action': 1,
            },
            {
                'state': 'five',
            },
            {
                'state': 'six',
            },
        ]

    Each dict is a state definition::

        {
            'state': 'one',
            'is_initial': True,
            'trigger': 1,
            'events': {
                True: 'two',
                False: 'three',
            },
        }

    The method :meth:`parse` produces ``HSMEStateChart`` instance with
    optimized transition map structure and some helpers.
    """

    STATE_CLS = HSMEState
    STATE_CHART_CLS = HSMEStateChart

    def __init__(self, chart=None):
        self.chart = chart or []
        if not isinstance(self.chart, collections.Iterable):
            raise HSMEParserError('Unexpected statechart object type')

    def get_chart_id(self, obj):
        return hashlib.md5(repr(obj).encode('utf8')).hexdigest()

    def parse(self):
        """Feel free to analyze this method if you want to create your own
        parser. Anyway you have to return the same ``HSMEStateChart`` structure.
        It's important to keep the ``parse`` method name to attach your custom
        parser later::

            hsme = HSMERunner()
            hsme.parse(TRANSITION_MAP, parser=YourCustomParserClass)
            hsme.start()

        :raises: ``HSMEParserError`` if wrong state definition or no initial
            state was found (or several of them).
        """
        states_map = {}
        initial_states = []
        final_states = []
        for state in self.chart:
            if 'state' not in state:
                raise HSMEParserError(
                    'No state label found in definition {0}'.format(repr(state))
                )
            state_id = state['state']
            state_inst = self.STATE_CLS(
                name=state_id,
                is_initial=state.get('is_initial', False),
                events=state.get('events'),
                trigger=state.get('trigger'),
                action=state.get('action'),
            )
            states_map[state_id] = state_inst
            if state_inst.is_initial:
                initial_states.append(state_inst)
            if state_inst.is_final:
                final_states.append(state_inst)

        if not len(initial_states):
            raise HSMEParserError(
                'No initial state found, mark you entry point state'
            )

        if len(initial_states) > 1:
            raise HSMEParserError(
                'Initial state ambiguity, you can have only one entry point'
            )

        initial_state = initial_states[0]

        events_map = {}
        for state_inst in states_map.values():
            for e, dst in state_inst.events.items():
                events_map.setdefault(e, {}).update({
                    state_inst: states_map[dst]
                })

        model = self.STATE_CHART_CLS(
            chart_id=self.get_chart_id(events_map),
            initial_state=initial_state,
            final_states=final_states,
            statechart=events_map,
        )

        return model
