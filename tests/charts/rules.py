# coding: utf-8


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


NO_INITIAL_RULES_CHART = [
    {
        'state': 'one',
        'events': {
            True: 'two',
        },
    },
    {
        'state': 'two',
    },
]


TWO_INITIAL_RULES_CHART = [
    {
        'state': 'one',
        'is_initial': True,
        'events': {
            True: 'two',
        },
    },
    {
        'state': 'two',
        'is_initial': True,
    },
]


BROKEN_RULES_CHART = [
    {
        'no_state': 'one',
    },
    {
        'state': 'two',
    },
]


MULTIPLE_TRIGGERS_RULES_CHART = [
    {
        'state': 'one',
        'is_initial': True,
        'trigger': [2, 1],
        'events': {
            False: 'two',
            True: 'three',
        },
    },
    {
        'state': 'two',
    },
    {
        'state': 'three',
    },
]
