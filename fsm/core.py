# coding=utf-8
import pickle
import datetime
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
        'datamodel',
        'src',
        'dst',
    ]
)


HSMEHistory = namedtuple(
    'HSMEHistory', [
        'timestamp',
        'event',
        'src',
        'dst',
        'status',
    ]
)


HSMEPickleFunc = namedtuple(
    'HSMEPickleFunc', [
        'sm_source',
        'sm_dest',
    ]
)


class HSMERunner(object):

    def __init__(self):
        self.clear()
        self.pickle_funcs = None

    def __getattribute__(self, name):
        if name in {
            'datamodel',
            'history',
            'in_state',
            'is_finished',
            'is_initial',
            'pickle',
            'start',
            'statechart_id',
            'update_datamodel',
        } and not self.is_loaded():
            raise HSMERunnerError("Initialize machine first")

        return object.__getattribute__(self, name)

    def is_loaded(self):
        return isinstance(self.hsme, HSMEStateChart)

    def is_started(self):
        return self.current_state is not None

    def clear(self):
        self.hsme = None
        self.processing_map = {}

    def start(self, data=None, autosave=True):
        if self.is_started():
            return False

        src = self.hsme._current_state
        dst = self.hsme._init_state
        hsme_proxy = HSMEProxyObject(
            fsm=self,
            event='__init__',
            src=src,
            dst=dst,
            data=data,
            datamodel=self.datamodel,
        )
        self._do_transition(hsme_proxy, autosave)

        return True

    def send(self, event_name, data=None, autosave=True):
        if not self.is_loaded() or not self.is_started():
            raise HSMERunnerError("Initialize and start machine first")

        src = self.current_state
        if not event_name in self.hsme._statechart:
            raise UnregisteredEventError(
                "Event %s is unregistered" % event_name
            )
        if not self.can_send(event_name):
            raise ImpossibleEventError(
                "Event %s is inappropriate in current state %s" % (
                    event_name, src.name
                )
            )
        event_transition = self.hsme._statechart[event_name]
        dst = src in event_transition and event_transition[src]

        hsme_proxy = HSMEProxyObject(
            fsm=self,
            event=event_name,
            data=data,
            datamodel=self.datamodel,
            src=src,
            dst=dst,
        )
        self._do_transition(hsme_proxy, autosave)

    def can_send(self, event_name):
        if not self.is_loaded() or event_name not in self.hsme._statechart:
            return False

        event_transition = self.hsme._statechart[event_name]

        return self.current_state in event_transition

    def get_possible_transitions(self):
        if self.is_loaded() and self.is_started():
            return self.current_state.events
        else:
            raise HSMERunnerError("Initialize and start machine first")

    def load(
        self,
        hsme_instance,
        autosave=True,
    ):
        # Save currently loaded statechart
        if autosave and self.is_loaded():
            self.flush()

        self.clear()

        if isinstance(hsme_instance, HSMEStateChart):
            self.hsme = hsme_instance
        elif isinstance(hsme_instance, basestring):
            self.hsme = pickle.loads(hsme_instance)
        else:
            raise HSMERunnerError(
                'Invalid statechart format, '
                'HSMEStateChart instance or pickle expected'
            )

        return self

    def pickle(self):
        return pickle.dumps(self.hsme)

    def flush(self):
        if self.pickle_funcs is None:
            raise HSMERunnerError(
                'Register source and dest callbacks '
                'for the pickle processing first'
            )

    def in_state(self, state_name):
        return self.current_state.name == state_name

    def is_finished(self):
        return (
            bool(self.hsme._final_state)
            and self.current_state == self.hsme._final_state
        )

    def is_initial(self):
        return (
            bool(self.current_state)
            and self.current_state.is_initial
        )

    @property
    def current_state(self):
        return self.hsme._current_state if self.hsme else None

    @property
    def datamodel(self):
        return self.hsme._datamodel

    def update_datamodel(self, data):
        self.hsme._datamodel.update(data)

    @property
    def history(self):
        return self.hsme._history

    @property
    def statechart_id(self):
        return self.hsme._id

    def register_pickle_funcs(self, sm_source, sm_dest):
        self.pickle_funcs = HSMEPickleFunc(
            sm_source=sm_source,
            sm_dest=sm_dest,
        )
        return self

    def register_processing_map(self, processing_map):
        self.processing_map = processing_map or {}
        return self

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

    def _do_transition(self, hsme_proxy, autosave=True):
        if hsme_proxy.src:
            src_callbacks = hsme_proxy.src.callbacks
            if hsme_proxy.src.name in self.processing_map:
                src_callbacks = self.processing_map[hsme_proxy.src.name]
            if 'on_exit' in src_callbacks:
                callback = self._prepare_callback(
                    src_callbacks['on_exit'],
                    hsme_proxy.src.name, 'on_exit',
                )
                callback(hsme_proxy)
            if 'on_change' in hsme_proxy.src.callbacks:
                callback = self._prepare_callback(
                    src_callbacks['on_change'],
                    hsme_proxy.src.name, 'on_change',
                )
                callback(hsme_proxy)

        if hsme_proxy.dst:
            dst_callbacks = hsme_proxy.dst.callbacks
            if hsme_proxy.dst.name in self.processing_map:
                dst_callbacks = self.processing_map[hsme_proxy.dst.name]
            if 'on_enter' in dst_callbacks:
                callback = self._prepare_callback(
                    dst_callbacks['on_enter'],
                    hsme_proxy.dst.name, 'on_enter',
                )
                callback(hsme_proxy)

            self.hsme._current_state = hsme_proxy.dst
            self._record_history(hsme_proxy, 'OK')

            if autosave:
                self.flush()

            if 'on_change' in dst_callbacks:
                callback = self._prepare_callback(
                    dst_callbacks['on_change'],
                    hsme_proxy.dst.name, 'on_change',
                )
                callback(hsme_proxy)

    def _record_history(self, hsme_proxy, status):
        self.hsme._history.append(
            HSMEHistory(
                timestamp=datetime.datetime.utcnow().isoformat(),
                event=hsme_proxy.event,
                src=hsme_proxy.src.name if hsme_proxy.src else None,
                dst=hsme_proxy.dst.name if hsme_proxy.dst else None,
                status=status,
            )
        )
