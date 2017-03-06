# coding: utf-8


SIMPLE_RULES_CHART = [
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
        'action': 2,
    },
    {
        'state': 'six',
        'action': 3,
    },
]


def one_is_one_trigger(proxy):
    return 1 == 1


def one_is_two_trigger(proxy):
    return 1 == 2


def two_is_two_trigger(proxy):
    return 2 == 2


def wrong_trigger(proxy):
    return 'wrong_event'


def pass_payload_action(proxy):
    print(proxy)


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
    return TRIGGERS_MAP.get(trigger_id)


def state_action_source(proxy, action_id):
    return ACTIONS_MAP.get(action_id)


TRIGGERS_MAP = {
    1: one_is_one_trigger,
    2: one_is_two_trigger,
    3: two_is_two_trigger,
}


ACTIONS_MAP = {
    1: pass_payload_action,
    2: insert_payload_action,
    3: insert_payload_action,
}
