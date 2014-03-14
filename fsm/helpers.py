# coding=utf-8
from fsm.core import HSMERunner, HSMERunnerError


class HSMERunnerMK(HSMERunner):

    def is_occupied_by(self, user_id):
        if not self.is_loaded():
            return False

        return self.datamodel.get('USER_ID') == user_id

    def load_by_ids(self, user_id, sm_name, autosave=True):
        sm_source = self.pickle_funcs.sm_source(
            user_id,
            sm_name,
        )
        return self.load(sm_source.pickle, autosave)

    def flush(self):
        super(HSMERunnerMK, self).flush()
        if self.is_loaded():
            sm_source = self.pickle_funcs.sm_source(
                self.datamodel.get('USER_ID'),
                self.datamodel.get('SM_NAME'),
            )
            self.pickle_funcs.sm_dest(
                sm=sm_source,
                hsme=self,
            )


class HSMERunnerFactory(object):

    def __init__(self, class_, amount):
        self.runners = frozenset({class_() for x in xrange(amount)})

    def get_free(self):
        for fsm in self.runners:
            if not fsm.is_loaded() and not fsm.is_started():
                return fsm
        return None

    def get_not_ids(self, user_id, sm_name):
        for fsm in self.runners:
            # currently occupied by requester
            if fsm.is_occupied_by(user_id) and fsm.statechart_id == sm_name:
                continue

            # strange, but possible
            if not fsm.is_loaded() or not fsm.is_started():
                return fsm

            # can be occupied by requester, but has another type
            if not fsm.is_occupied_by(user_id) or fsm.statechart_id != sm_name:
                return fsm

        raise HSMERunnerError('Something is wrong')

    def get_not_inst(self, fsm_inst):
        for fsm in self.runners:
            if fsm_inst is fsm:
                continue
            return fsm

        raise HSMERunnerError('Something is wrong')

    def get_current(self, user_id, sm_name):
        for fsm in self.runners:
            if fsm.is_occupied_by(user_id) and fsm.statechart_id == sm_name:
                return fsm

        return None

    def get_current_or_load(self, user_id, sm_name, autosave=True):
        fsm = self.get_current(user_id, sm_name)
        if fsm is None:
            fsm = self.get_not_ids(user_id, sm_name)
            fsm.load_by_ids(user_id, sm_name, autosave)
        return fsm

    def register_pickle_funcs(self, sm_source, sm_dest):
        for fsm in self.runners:
            fsm.register_pickle_funcs(sm_source, sm_dest)
