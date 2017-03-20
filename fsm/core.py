# coding: utf-8
import calendar
import json
import time
from collections import namedtuple

from fsm.parsers import HSMEStateChart, HSMEDictsParser


class HSMERunnerError(Exception):
    """Raised if ``HSMERunner`` receives invalid data
    or model-sensitive methods called before model load/start.
    """


class HSMEWrongEventError(Exception):
    """Raised if ``HSMERunner`` receives inappropriate transition event
    for the current state.
    """


class HSMEWrongTriggerError(HSMEWrongEventError):
    """Raised if some trigger produces invalid or inappropriate
    transition event inside some state and such a transition is impossible.
    """


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
    """FSM (Finite State Machine) model (transition map) *runner*,
    provides high-level API to work with declared states, makes transitions,
    tracks transition history, etc.

    :param trigger_source: the callback, that produces event for the
        current state, can be defined and used to create self-transition
        flow instead of manual external event sending.

    :param action_source: the callback, that produces some side effect
        inside related state. Something like logging, processing,
        DB reads/writes, etc.
    """

    STATE_CHART_CLS = HSMEStateChart

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
            'dump',
            'get_possible_transitions',
            'history',
            'send',
            'start',
        ]) and not self.is_loaded():
            raise HSMERunnerError('Load machine first')

        if name in set([
            'can_send',
            'in_state',
            'is_finished',
        ]) and not self.is_started():
            raise HSMERunnerError('Start machine first')

        return object.__getattribute__(self, name)

    def __repr__(self):
        if self.is_loaded():
            return 'HSMERunner: {0}'.format(self.model.chart_id)
        else:
            return 'HSMERunner: empty'

    def load(self, model=None, deserializer=None):
        """Can be used to *load* some serialized FSM model object,
        to continue machine executing::

            hsme = HSMERunner()
            hsme.parse(RULES_CHART)
            serialized_hsme = hsme.dump()

            hsme_2 = HSMERunner()
            hsme_2.load(serialized_hsme)

        :param model: serialized FSM model object.
        :param deserializer: some callable, ``json.loads`` replacement.
        :returns: HSMERunner instance with *loaded* FSM model.
        """
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
        """Can be used to *dump* (serialize, pickle, up to you) some loaded
        FSM model to take and reload it in the future::

            hsme = HSMERunner()
            hsme.parse(RULES_CHART)
            serialized_hsme = hsme.dump()

            hsme_2 = HSMERunner()
            hsme_2.load(serialized_hsme)

        :param serializer: some callable, ``json.dumps`` replacement.
        :returns: JSON string (by default).
        """
        serializer = serializer or json.dumps
        return serializer(self.model.as_dict())

    def parse(self, chart, parser=None):
        """FSM transition map initial processing and loading::

            RULES_CHART = [
                {
                    'state': 'one',
                    'is_initial': True,
                    'events': {
                        True: 'two',
                        False: 'three',
                    },
                },
                {
                    'state': 'two',
                },
                {
                    'state': 'three',
                },
            ]
            hsme = HSMERunner()
            hsme.parse(RULES_CHART)
            hsme.is_loaded() == True

        Internal transition map representation is more verbose but more
        efficient in relationship lookups ``O(1)``, so parsing is important
        and is the first step if you create new machine from transition map
        declaration.

        :param chart: transition map object, states and events definition.
        :param parser: ``HSMEDictsParser``, by default. If custom, the class
            has to implement the :meth:`parse()` method and produce proper
            internal structure, the same as in original ``HSMEDictsParser``.
        :returns: HSMERunner instance with *loaded* FSM model.
        """
        parser = parser or HSMEDictsParser
        model = parser(chart).parse()
        return self.load(model)

    def is_loaded(self):
        """Checks if Runner is *loaded* with some model after the :meth:`load` or
        the :meth:`parse` method call. Means you can *start* machine and produce
        some events/transitions with loaded model.

        :returns: True or False.
        """
        return self.model is not None

    def is_started(self):
        """Checks if Runner is *loaded* with some model and *started*.
        Means that your machine was set to it's initial state (entry point)
        or already had some transitions (current state points to some state).

        :returns: True or False
        """
        return self.current_state is not None

    def start(self, payload=None):
        """Starts machine if Runner is loaded with some model.
        If the model has never been started yet, Runner goes to the
        initial state. Does nothing if the model is already started::

            hsme = HSMERunner()
            hsme.parse(RULES_CHART)
            hsme.start()
            hsme.is_started() == True

        :param payload: any data, can be used inside triggers and actions.
        :returns: True if initial transition was completed at a first time.
        """
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
        """The most important part of the Runner API. Several conditions have to
        be met for successful state transition. Sure, Runner has to be
        loaded with FSM model, model itself has to be started and ``event_name``
        has to be present in events map declaration of the current state::

            RULES_CHART = [
                {
                    'state': 'one',
                    'is_initial': True,
                    'events': {
                        True: 'two',
                        False: 'three',
                    },
                },
                {
                    'state': 'two',
                },
                {
                    'state': 'three',
                },
            ]
            hsme = HSMERunner()
            hsme.parse(RULES_CHART)  # parsing and loading
            hsme.start()  # go to initial state (``is_initial`` marker)
            hsme.send(True)  # go to step 'two'
            hsme.in_state('two') == True

        Raises ``HSMEWrongEventError`` exception if transition map has no
        mapping for the called event::

            hsme.in_state('two') == True
            hsme.send('wrong_event')  # raises HSMEWrongEventError

        :param event_name: any serializable object, usually string,
            digit or bool value. Create your own convention and follow it.
        :param payload: any data, can be used inside triggers and actions
        :returns: True if transition was completed successfully
        """
        src = self.current_state
        if event_name not in self.model.statechart:
            raise HSMEWrongEventError(
                'Event {0} is unregistered'.format(
                    repr(event_name)
                )
            )
        if not self.can_send(event_name):
            raise HSMEWrongEventError(
                'Event {0} is inappropriate for the current state {1}'.format(
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
        """Checks if you can apply some event for the current state.

        :param event_name: some event name.
        :returns: True if you can.
        """
        if event_name not in self.model.statechart:
            return False

        event_transition = self.model.statechart[event_name]

        return self.current_state in event_transition

    def get_possible_transitions(self):
        """Useful if you have started FSM model in some state and have no idea
        where you can go from this point::

            hsme = HSMERunner()
            hsme.parse(RULES_CHART)
            hsme.start()

            print(hsme.get_possible_transitions())
            >> {True: 'two', False: 'three'}

        :returns: ``{'event': 'state'}`` mapping.
        """
        return self.current_state.events

    def in_state(self, state_name):
        """Just an alias for the direct comparison. Checks if your current
        state is exactly that state.

        :param state_name: state name/id.
        :returns: True or False.
        """
        return self.current_state.name == state_name

    def is_finished(self):
        """If some state has no events mapping, machine can't go somewhere from
        such a state. It's a leaf of the FSM graph.

        :returns: True or False.
        """
        return (
            bool(self.model.final_states) and
            self.current_state in self.model.final_states
        )

    @property
    def current_state(self):
        return self.model.current_state if self.model else None

    @property
    def history(self):
        """Really helpful feature for debugging and testing. Draws transitions
        as a vector::

            hsme = HSMERunner(trigger_source=event_trigger_source)
            hsme.parse(RULES_CHART)
            hsme.start()
            hsme.send(True)  # go to state "two"
            hsme.send(False)  # go to state "five"

            print(hsme.history)
            >> HSMEStateChart: db5e920ca6b236bd58ba369fbf0a320e =>
               (one:None @1489430643) ->
               (two:True @1489430643) ->
               (five:False @1489430643)

        You can see the ``(state:event @unixtimestamp)`` groups
        and actual transition flow, from left to right.
        """
        if self.model and self.model.history:
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
            self.action_source(hsme_proxy, dst.action)

        if dst.trigger and self.trigger_source:
            trigger_event = self.trigger_source(hsme_proxy, dst.trigger)
            if not self.can_send(trigger_event):
                raise HSMEWrongTriggerError(
                    'Event {0} is inappropriate for '
                    'the current state {1}'.format(
                        repr(trigger_event),
                        repr(self.model.current_state),
                    )
                )

            return self.send(trigger_event, hsme_proxy.payload)

        return True
