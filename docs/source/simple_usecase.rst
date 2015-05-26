.. _simple_usecase:

Использование 
=============

Пример работы с FSM на базе описанной в формате XML таблицы переходов [#x1]_.

.. code-block:: python

    hsme_runner = HSMERunner()
    statechart = HSMEXMLParser.parse_from_path(chart='path/to/basket.xml')

    hsme_runner.load(statechart)
    hsme_runner.start()
    hsme_runner.send('event_name', data={'user': user_obj})

.. [#x1] :ref:`xml_format`
.. [#x2] :ref:`runner_api`
