SIMPLE_CHECKOUT = [
    {
        'id': 'in_frontpage',
        'initial': True,
        'events': {
            'do_add_to_busket': 'in_busket',
            'do_goto_busket': 'in_busket',
            'do_goto_frontpage': 'in_frontpage',
            'do_goto_product_page': 'in_product',
        },
    },
    {
        'id': 'in_product', # META STATE
        'events': {
            '~do_goto_in_product_normal': 'in_product_normal',
            '~do_goto_in_product_unavailable': 'in_product_unavailable',
            '~do_goto_in_product_reserved': 'in_product_reserved',
        },
    },
    {
        'id': 'in_product_normal',
        'events': {
            'do_add_to_busket': 'in_busket',
            'do_goto_busket': 'in_busket',
            'do_goto_frontpage': 'in_frontpage',
            'do_goto_product_page': 'in_product',
        },
    },
    {
        'id': 'in_product_unavailable',
        'events': {
            'do_goto_busket': 'in_busket',
            'do_goto_frontpage': 'in_frontpage',
            'do_goto_product_page': 'in_product',
        },
    },
    {
        'id': 'in_product_reserved',
        'events': {
            'do_goto_busket': 'in_busket',
            'do_goto_frontpage': 'in_frontpage',
            'do_goto_product_page': 'in_product',
        },
    },
    {
        'id': 'in_busket',  # META STATE
        'events': {
            '~do_goto_full_busket': 'in_busket_normal',
            '~do_goto_empty_busket': 'in_busket_empty',
        },
    },
    {
        'id': 'in_busket_normal',
        'events': {
            'do_goto_product_page': 'in_product',
            'do_goto_frontpage': 'in_frontpage',
            'do_create_order': 'in_order_info_processing',
            'do_remove_product': 'in_busket',
        },
    },
    {
        'id': 'in_busket_empty',
        'events': {
            'do_goto_frontpage': 'in_frontpage',
        },
    },
    {
        'id': 'in_order_info_processing',
        'events': {
            'do_goto_busket': 'in_busket',
        },
        'final': True,
    },
]
