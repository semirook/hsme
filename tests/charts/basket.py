BASKET_CHART = [
    {
        'id': 'in_recalculation',  # META STATE
        'events': {
            'do_goto_normal_basket': 'in_basket_normal',
            'do_goto_empty_basket': 'in_basket_empty',
            'do_goto_basket_freeze': 'in_basket_freeze',
        },
    },
    {
        'id': 'in_basket_normal',
        'events': {
            'do_goto_normal_basket': 'in_recalculation',
            'do_add_to_basket': 'in_recalculation',
            'do_remove_product': 'in_recalculation',
        },
    },
    {
        'id': 'in_basket_freeze',
        'events': {
            'do_goto_basket_freeze': 'in_recalculation',
            'do_add_to_basket': 'in_recalculation',
            'do_remove_product': 'in_recalculation',
        },
    },
    {
        'id': 'in_basket_empty',
        'initial': True,
        'events': {
            'do_add_to_basket': 'in_recalculation',
        },
    },
]
