# coding: utf-8
import pickle
import types
from collections import namedtuple

from fsm.parsers import HSMEStateChart
from fsm.utils import ImportStringError, import_string


class HSMERunnerError(Exception):
    pass


class ImpossibleEventError(Exception):
    pass


class UnregisteredEventError(Exception):
    pass


class StateConditionError(Exception):
    pass


HSMEProxyObject = namedtuple(
    'HSMEProxyObject', [
        'fsm',
        'event',
        'data',
        'src',
        'dst',
    ]
)


class HSMERunner(object):

    def __init__(self):
        self.clear()

    def __getattribute__(self, name):
        if name in set([
            'datamodel',
            'in_state',
            'is_finished',
            'is_initial',
            'save',
            'start',
            'statechart_id',
        ]) and not self.is_loaded():
            raise HSMERunnerError("Initialize machine first")

        return object.__getattribute__(self, name)

    def is_loaded(self):
        return self.model is not None

    def is_started(self):
        return self.current_state is not None

    def clear(self):
        self.model = None

    def start(self, data=None):
        if self.is_started():
            return False

        src = self.model._current_state
        dst = self.model._init_state
        hsme_proxy = HSMEProxyObject(
            fsm=self,
            event='__init__',
            src=src,
            dst=dst,
            data=data,
        )
        self._do_transition(hsme_proxy)

        return True

    def send(self, event_name, data=None):
        if not self.is_loaded() or not self.is_started():
            raise HSMERunnerError("Initialize and start machine first")

        src = self.current_state
        if event_name not in self.model._statechart:
            raise UnregisteredEventError(
                "Event %s is unregistered" % event_name
            )
        if not self.can_send(event_name):
            raise ImpossibleEventError(
                "Event %s is inappropriate in current state %s" % (
                    event_name, src.name
                )
            )
        event_transition = self.model._statechart[event_name]
        dst = src in event_transition and event_transition[src]

        hsme_proxy = HSMEProxyObject(
            fsm=self,
            event=event_name,
            data=data,
            src=src,
            dst=dst,
        )
        self._do_transition(hsme_proxy)

    def can_send(self, event_name):
        if not self.is_loaded() or event_name not in self.model._statechart:
            return False

        event_transition = self.model._statechart[event_name]

        return self.current_state in event_transition

    def get_possible_transitions(self):
        if self.is_loaded() and self.is_started():
            return self.current_state.events
        else:
            raise HSMERunnerError("Initialize and start machine first")

    def load(self, model=None):
        self.clear()
        if isinstance(model, bytes):
            model = pickle.loads(model)
        if not isinstance(model, HSMEStateChart):
            raise HSMERunnerError(
                'Invalid statechart format, '
                'HSMEStateChart instance expected'
            )
        self.model = model

        return self

    def save(self):
        return pickle.dumps(self.model)

    def in_state(self, state_name):
        return self.current_state.name == state_name

    def is_finished(self):
        return (
            bool(self.model._final_state)
            and self.current_state == self.model._final_state
        )

    def is_initial(self):
        return (
            bool(self.current_state)
            and self.current_state.is_initial
        )

    @property
    def current_state(self):
        return self.model._current_state if self.model else None

    @property
    def statechart_id(self):
        return self.model._id

    @property
    def datamodel(self):
        return self.model._datamodel

    def _prepare_callback(self, callback, state, type_):
        if not isinstance(callback, types.FunctionType):
            try:
                callback = import_string(callback)
            except ImportStringError:
                raise ImportError(
                    'Callback "%s" for the state "%s::%s" not found' % (
                        callback, state, type_
                    )
                )
        return callback

    def _do_transition(self, hsme_proxy):
        if hsme_proxy.src:
            src_callbacks = hsme_proxy.src.callbacks
            if 'on_exit' in src_callbacks:
                callback_exit = self._prepare_callback(
                    src_callbacks['on_exit'],
                    hsme_proxy.src.name, 'on_exit',
                )
                callback_exit(hsme_proxy)

        if hsme_proxy.dst:
            dst_callbacks = hsme_proxy.dst.callbacks
            if 'on_enter' in dst_callbacks:
                callback_enter = self._prepare_callback(
                    dst_callbacks['on_enter'],
                    hsme_proxy.dst.name, 'on_enter',
                )
                callback_enter(hsme_proxy)

            self.model._current_state = hsme_proxy.dst

            if 'on_change' in dst_callbacks:
                callback_change = self._prepare_callback(
                    dst_callbacks['on_change'],
                    hsme_proxy.dst.name, 'on_change',
                )
                callback_change(hsme_proxy)
