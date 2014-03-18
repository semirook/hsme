.. _simple_usecase:

Использование 
=============

Рассмотрим пример работы с FSM на базе описанной в формате XML таблицы переходов [#x1]_.

В наиболее простом случае, достаточно одного runner`а [#x2]_

.. code-block:: python

    hsme_runner = HSMERunner()
    statechart = HSMEXMLParser(
        doc='path/to/basket.xml',
        doc_id='basket',
        datamodel={'a': 1, 'b': 2},
    ).parse()

    hsme_runner.load(statechart, autosave=False)
    hsme_runner.start(autosave=False)
    hsme_runner.send('event_name', data={'user': request.user}, autosave=False)

.. [#x1] :ref:`xml_format`
.. [#x2] :ref:`runner_api`
