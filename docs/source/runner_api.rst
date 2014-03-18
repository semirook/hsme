.. _runner_api:

HSMERunner API
==============

**HSMERunner** – класс, который является набором API-методов для общения с FSM-объектом [#f1]_, с помощью которых можно загружать/выгружать FSM-объект, посылать события на изменение его состояния, снимать определённые значения, историю переходов, получить список возможных переходов из текущего состояния и пр. HSMERunner – универсальная обёртка вокруг FSM-объекта, знает о его внутренней структуре, но не зависит от его типа и таблицы переходов [#f2]_. 

В следущих примерах, предполагается работа с таблицей переходов basket из `basket.xml`.

* **hsme_runner** – экземпляр класса HSMERunner
* **fsm** – FSM-объект (экземпляр класса HSMEStateChart)

.. code-block:: python 

    hsme_runner = HSMERunner()
    fsm = HSMEXMLParser(
        doc='path/to/basket.xml',
        doc_id='basket',
    ).parse()


.. [#f1] FSM – Final State Machine. Объект, который включает в себя информацию об идентификаторе, текущем, начальном и конечном состоянии, нормализованную таблицу переходов, историю переходов и модель данных. Экземпляр класса HSMEStateChart, создаётся парсером (HSMEDictsParser или HSMEXMLParser) на базе таблицы переходов и пользовательских данных.
.. [#f2] Таблица переходов – формализованное описание состояний конечного автомата и событий (входного алфавита), на которые реагируют эти состояния. Правила переходов между состояниями.


can_send(event_name)
--------------------
Проверяет возможность отправить событие (event_name), находясь в текущем состоянии::

    hsme_runner.can_send('do_add_to_busket')  # True or False


clear()
-------
Обычно не используется явно, обнуляет состояние runner`а, таким образом выгружая FSM-объект и карту перекрывающих callback`ов::

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
Возвращает словарь, модель данных FSM, если она была определена во время парсинга таблицы переходов или загружена позже методом :meth:`update_datamodel` (так как это просто словарь, можно работать с ним методами dict). Вызовет исключение HSMERunnerError, если машина не загружена::

    hsme_runner.load(fsm)  # если не было загружено раньше
    fsm_datamodel = hsme_runner.datamodel 


flush()
-------
Обычно не требует явного вызова. Выбрасывает исключение HSMERunnerError, если не были определены и зарегистрированы методом :meth:`register_pickle_funcs` функции источника и сохранения FSM-объекта. Параметры, необходимые для передачи в эти функции заранее неизвестны, поэтому flush() требуется доопределить через наследование::

    class HSMERunnerMK(HSMERunner):

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

Данный пример реализации предполагает наличие в модели данных FSM идентификаторов пользователя и названия-метки машины, которые позволяют однозначно определить объект. Сами callback`и в простом случае могут выглядеть так::

    def statemachine_save(sm, hsme):
        sm.pickle = hsme.pickle()
        sm.save()

    def statemachine_source(user_id, sm_name):
        return StateMachine.query.filter_by(user_id=user_id, name=sm_name).first()


get_possible_transitions()
--------------------------
Возвращает словарь вида {'event_name': 'state_name'} с соответствующими значениями для текущего состояния машины. Вызывает исключение HSMERunnerError, если машина на загружена и не запущена методами :meth:`load` и :meth:`start` соответственно::

    hsme_runner.load(fsm)
    hsme_runner.start()
    hsme_runner.get_possible_transitions()
    # {
    #    'do_goto_in_basket_normal': 'in_basket_normal',
    #    'do_goto_in_basket_empty': 'in_basket_empty',
    #    'do_goto_in_basket_freeze': 'in_basket_freeze',
    # }


history
-------
Возвращает список объектов типа HSMEHistory, включающие в себя атрибуты `timestamp`, `event`, `src`, `dst`, `status`. Вызывает исключение HSMERunnerError, если машина не загружена::

    hsme_runner.load(fsm)

И имеет смысл, если запущена::

    hsme_runner.start()
    hsme_runner.send('do_add_to_basket', data={...})
    hsme_runner.history
    # [
    #     HSMEHistory(timestamp='2014-03-18T10:46:30.629432', event='do_add_to_basket', src='in_basket_empty', dst='in_recalculation', status='OK')
    #     HSMEHistory(timestamp='2014-03-18T10:46:30.637123', event='do_goto_in_basket_normal', src='in_recalculation', dst='in_basket_normal', status='OK')
    # ]


in_state(state_name)
--------------------
Проверяет в каком состоянии находится машина::

    hsme_runner.in_state('in_frontpage')

Вызывает исключение HSMERunner, если машина не загружена. По факту, просто синтаксический сахар вокруг конструкции::

    hsme_runner.current_state.name == 'in_frontpage'


is_finished()
-------------
Булевая проверка на конечное состояние FSM. Предполагает, что в таблице переходов определёно такое состояние и возвращает True, если текущее состояние машины совпадает с конечным. Вызывает исключение HSMERunner, если машина не загружена::

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


load(fsm, [autosave=True])
--------------------------
Загружает в runner FSM-объект типа HSMEStateChart или его pickle. Если runner в это время уже загружен каким-либо другим экземпляром, происходит сброс вызовом :meth:`flush` (если зарегистрированы pickle-callback`и), обнуление и загрузка нового экземпляра::

    hsme_runner.load(fsm)  # устанавливает fsm
    hsme_runner.load(another_fsm)  # сохраняет (опционально) состояние fsm, загружает another_fsm


pickle()
--------
Возвращает pickle загруженной FSM::

    hsme_runner.load(fsm)
    pickle_bytestring = hsme_runner.pickle()


register_pickle_funcs(sm_source, sm_dest)
-----------------------------------------
Прежде, чем использовать возможность autosave`а методов :meth:`load`, :meth:`save`, :meth:`send` и метода :meth:`flush` в частности, необходимо зарегистрировать функции источника и сохранения FSM-объектов. Смотрите пример метода :meth:`flush`. После регистрации, функции доступны из runner`а::

    hsme_runner.register_pickle_funcs(
        sm_source=statemachine_source,
        sm_dest=statemachine_save,
    )
    sm_source = hsme_runner.pickle_funcs.sm_source
    sm_dest = hsme_runner.pickle_funcs.sm_dest


register_processing_map(mapping)
--------------------------------
Используется для возможности определить callback`и состояний или перекрыть их определения из таблицы переходов. Принимает в качестве аргумента словарь, где ключи – названия состояний, чьи callback`и мы хотим определить, а значения – словари вида {тип [#r1]_: callback}::

    CUSTOM_BASKET_CALLBACKS = {
        'in_basket_normal': {
            'on_enter': on_enter_in_basket,
            'on_change': on_change_in_basket,
        },
        'in_basket_empty': {
            'on_exit': on_exit_from_basket_empty,
        },
    }
    hsme_runner.register_processing_map(CUSTOM_BASKET_CALLBACKS)

В качестве описания callback`ов могут также выступать строки с абсолютным путём к функции (в python-стиле), вместо объекта функции. Во время отработки они будут импортированы динамически::

    CUSTOM_BASKET_CALLBACKS = {
        'in_basket_normal': {
            'on_enter': 'package.module.on_enter_in_basket',
            'on_change': package.module.on_change_in_basket',
        },
        'in_basket_empty': {
            'on_exit': 'package.module.on_exit_from_basket_empty',
        },
    }
    hsme_runner.register_processing_map(CUSTOM_BASKET_CALLBACKS)

В случае, если в таблице переходов определена логика для состояния, которую мы хотим перекрыть, нужно помнить, что перекрытие полное, а не частичное. Например::

    <state id="in_recalculation" targetns="tests.charts.basket_callbacks">
        <onentry target="on_enter_in_recalculation"/>
        <onchange target="on_change_in_recalculation"/>
        <onexit target="on_exit_in_recalculation"/>
    </state>

    CUSTOM_BASKET_CALLBACKS = {
        'in_recalculation': {
            'on_enter': 'package.module.another_callback'
        }
    }
    hsme_runner.register_processing_map(CUSTOM_BASKET_CALLBACKS)

Для состояния *in_recalculation* останется доступным только один новый callback на **on_enter**. Поэтому если возникает необходимость сохранить остальные, надо дополнить список, согласно данным из таблицы переходов::

    CUSTOM_BASKET_CALLBACKS = {
        'in_recalculation': {
            'on_enter': 'package.module.another_callback'
            'on_change': 'tests.charts.basket_callbacks.on_change_in_recalculation',
            'on_exit': 'tests.charts.basket_callbacks.on_exit_in_recalculation',
        }
    }
    hsme_runner.register_processing_map(CUSTOM_BASKET_CALLBACKS)


.. [#r1] Типов callback`ов предусмотрено 3: на вход в состояние ('on_enter'), на состояние ('on_change') и на выход из состояния ('on_exit')


send(event_name, [data=None, autosave=True])
--------------------------------------------
Главный инструмент для общения с FSM. Предполагается, что машина загружена и запущена. Делает попытку изменить состояние машины по указанному событию. Опционально, можно передать данные callback`ам в виде словаря. Если таблица переходов ничего не знает об отправляемом событии, вернёт исключение UnregisteredEventError. Если событие не предусмотрено описанием текущего состояния, вернёт исключение ImpossibleEventError::

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

По факту, происходит transition (перемещение) из текущего состояния в состояние, которое соответствует событию. При этом, последовательно отрабатывают callback`и на выход из текущего состояния, попытку входа в следующее состояние и вход в следующее состояние (при условии, что такие callback`и определены и данная цепочка не прервана исключением на одном из этих этапов)::

    hsme_runner.in_state('in_basket_empty')  # True
    hsme_runner.send('do_add_to_basket')

    # 1. Callback on_exit состояния in_basket_empty 
    # 2. Callback on_enter состояния in_basket_normal
    # 3. Смена состояния на in_basket_normal
    # 4. Callback on_change состояния in_basket_normal

    hsme_runner.in_state('in_basket_normal')


start([data=None, autosave=True])
---------------------------------
Метод "запускает" загруженный FSM-объект, переводя его в начальное состояние. Является частным случаем метода :meth:`send`, в отличие от которого не принимает событие в качестве аргумента, а переводит FSM в начальное состояние во внутреннему событию. Если FSM уже запущен и находится в каком-либо состоянии, метод вернёт False. Так же, как и send(), принимает в качестве опционального аргумента данные на transition, которые могут быть обработаны callback`ами начального состояния::

    hsme_runner.load(fsm)
    hsme_runner.start(data={'params': params})

    # 1. Callback on_enter состояния in_basket_empty
    # 2. Смена состояния на in_basket_empty
    # 3. Callback on_change состояния in_basket_empty

    hsme_runner.is_started()  # True
    hsme_runner.in_state('in_basket_empty')  # True
    

statechart_id
-------------
Возвращает строковый идентификатор FSM-объекта, который был указан во время парсинга таблицы переходов. Если `doc_id` указан не был – вернёт md5-сумму представления таблицы переходов::

    hsme_runner = HSMERunner()
    fsm = HSMEXMLParser(
        doc='path/to/basket.xml',
        doc_id='basket',
    ).parse()

    hsme_runner.statechart_id  # 'basket'


update_datamodel(data)
----------------------
Обновляет (update словаря) модель данных FSM-объекта::

    hsme_runner.datamodel  # {}
    hsme_runner.update_datamodel({'a': 1, 'b': 2})
    hsme_runner.datamodel  # {'a': 1, 'b': 2}
