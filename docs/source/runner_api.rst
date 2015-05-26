.. _runner_api:

HSMERunner API
==============

**HSMERunner** – класс, который является набором API-методов для общения с FSM-объектом [#f1]_, 
с помощью которых можно загружать/выгружать FSM-объект, посылать события на изменение его состояния, 
снимать определённые значения, историю переходов, получить список возможных переходов из текущего состояния и пр. 
HSMERunner – универсальная обёртка вокруг FSM-объекта, знает о его внутренней структуре, но не зависит от его типа 
и таблицы переходов [#f2]_. 

В следущих примерах, предполагается работа с таблицей переходов basket из `basket.xml`.

* **hsme_runner** – экземпляр класса HSMERunner
* **fsm** – FSM-объект (экземпляр класса HSMEStateChart)

.. code-block:: python 

    hsme_runner = HSMERunner()
    fsm = HSMEXMLParser.parse_from_path(chart='path/to/basket.xml')


.. [#f1] FSM – Final State Machine. Объект, который включает в себя информацию об идентификаторе, 
    текущем, начальном и конечном состоянии, нормализованную таблицу переходов и модель данных. 
    Экземпляр класса HSMEStateChart, создаётся парсером (HSMEDictsParser или HSMEXMLParser) 
    на базе таблицы переходов и пользовательских данных.
.. [#f2] Таблица переходов – формализованное описание состояний конечного автомата и событий (входного алфавита), 
    на которые реагируют эти состояния. Правила переходов между состояниями.


can_send(event_name)
--------------------
Проверяет возможность отправить событие (event_name), находясь в текущем состоянии::

    hsme_runner.can_send('do_add_to_busket')  # True or False


clear()
-------
Обычно не используется явно, обнуляет состояние runner`а, таким образом выгружая FSM-объект::

    hsme_runner.clear()


current_state
-------------
Возвращает объект типа HSMEState, если машина загружена и запущена, иначе None::

    if hsme_runner.current_state is not None:
        in_proper_state = hsme_runner.current_state.name in {'in_busket_normal', 'in_basket_freeze'}
    else:
        in_proper_state = False


datamodel
---------
Возвращает словарь, модель данных FSM. Вызовет исключение HSMERunnerError, если машина не загружена::

    hsme_runner.load(fsm)  # если не было загружено раньше
    fsm_datamodel = hsme_runner.datamodel 


get_possible_transitions()
--------------------------
Возвращает словарь вида {'event_name': 'state_name'} с соответствующими значениями для текущего состояния машины. 
Вызывает исключение HSMERunnerError, если машина на загружена и не запущена методами :meth:`load` и :meth:`start` соответственно::

    hsme_runner.load(fsm)
    hsme_runner.start()
    hsme_runner.get_possible_transitions()
    # {
    #    'do_goto_in_basket_normal': 'in_basket_normal',
    #    'do_goto_in_basket_empty': 'in_basket_empty',
    #    'do_goto_in_basket_freeze': 'in_basket_freeze',
    # }


in_state(state_name)
--------------------
Проверяет в каком состоянии находится машина::

    hsme_runner.in_state('in_frontpage')

Вызывает исключение HSMERunner, если машина не загружена. По факту, просто синтаксический сахар вокруг конструкции::

    hsme_runner.current_state.name == 'in_frontpage'


is_finished()
-------------
Булевая проверка на конечное состояние FSM. Предполагает, что в таблице переходов определёно такое состояние 
и возвращает True, если текущее состояние машины совпадает с конечным. Вызывает исключение HSMERunner, если машина не загружена::

    hsme_runner.is_finished()  # True or False


is_initial()
------------
По аналогии с is_finished(), проверяет FSM на начальное состояние::

    hsme_runner.is_initial()  # True or False


is_loaded()
-----------
Индикатор загрузки runner`а FSM-объектом::

    hsme_runner.is_loaded()  # False
    hsme_runner.load(fsm)
    hsme_runner.is_loaded()  # True


is_started()
------------
Индикатор работы runner`а. Означает, что FSM находится в каком-то состоянии и может принимать события::

    hsme_runner.load(fsm)
    hsme_runner.is_loaded()  # True
    hsme_runner.is_started()  # False

    hsme_runner.start()
    hsme_runner.is_started()  # True


load(fsm)
--------------------------
Загружает в runner FSM-объект типа HSMEStateChart или его pickle. Если runner в это время уже загружен 
каким-либо другим экземпляром, происходит его обнуление и загрузка нового экземпляра::

    hsme_runner.load(fsm)  # устанавливает fsm
    hsme_runner.load(another_fsm)  # загружает another_fsm


save()
------
Возвращает pickle загруженной FSM::

    hsme_runner.load(fsm)
    pickle_bytestring = hsme_runner.pickle()


send(event_name, [data=None])
-----------------------------
Главный инструмент для общения с FSM. Предполагается, что машина загружена и запущена. 
Делает попытку изменить состояние машины по указанному событию. Опционально, можно передать данные 
callback`ам в виде словаря. Если таблица переходов ничего не знает об отправляемом событии, 
вернёт исключение UnregisteredEventError. Если событие не предусмотрено описанием текущего состояния, 
вернёт исключение ImpossibleEventError::

    hsme_runner.send(
        'do_add_to_basket', data={
            'params': params,
        }
    )
 
Во избежание оборачивания в try/except блок, рекомендуется использовать в паре с can_send()::

    if hsme_runner.can_send('do_add_to_basket'):
        hsme_runner.send(
            'do_add_to_basket', data={
                'params': params,
            }
        )

По факту, происходит transition (перемещение) из текущего состояния в состояние, 
которое соответствует событию. При этом, последовательно отрабатывают callback`и на выход из текущего состояния, 
попытку входа в следующее состояние и вход в следующее состояние (при условии, что такие callback`и определены 
и данная цепочка не прервана исключением на одном из этих этапов)::

    hsme_runner.in_state('in_basket_empty')  # True
    hsme_runner.send('do_add_to_basket')

    # 1. Callback on_exit состояния in_basket_empty 
    # 2. Callback on_enter состояния in_basket_normal
    # 3. Смена состояния на in_basket_normal
    # 4. Callback on_change состояния in_basket_normal

    hsme_runner.in_state('in_basket_normal')


start([data=None])
------------------
Метод "запускает" загруженный FSM-объект, переводя его в начальное состояние. 
Является частным случаем метода :meth:`send`, в отличие от которого не принимает событие в качестве аргумента, 
а переводит FSM в начальное состояние во внутреннему событию. Если FSM уже запущен и находится в каком-либо состоянии, 
метод вернёт False. Так же, как и send(), принимает в качестве опционального аргумента данные на transition, 
которые могут быть обработаны callback`ами начального состояния::

    hsme_runner.load(fsm)
    hsme_runner.start(data={'params': params})

    # 1. Callback on_enter состояния in_basket_empty
    # 2. Смена состояния на in_basket_empty
    # 3. Callback on_change состояния in_basket_empty

    hsme_runner.is_started()  # True
    hsme_runner.in_state('in_basket_empty')  # True
    

statechart_id
-------------
Возвращает строковый идентификатор FSM-объекта (md5-сумма представления таблицы переходов)::
