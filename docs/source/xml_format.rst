.. _xml_format:

Описание таблицы переходов в XML
================================

Реальный пример описания таблицы переходов с callback`ами для реализации логики компонента "Корзина":

.. literalinclude:: ../../tests/charts/basket.xml
   :language: xml


Базовые принципы и возможности предложенного формата
----------------------------------------------------

Формат описания является подмножеством стандарта `State Chart XML (SCXML) <http://www.w3.org/TR/scxml/>`_ 
с некоторыми ограничениями и дополнениями. О них подробнее будет описано ниже.

<state>
~~~~~~~

Тег **<state>** описывает состояние конечного автомата. Формальный список возможных атрибутов:

=============== ============= ============================================== ==========================================
Название        Обязательный  Значения                                       Описание
=============== ============= ============================================== ==========================================
``id``          да            любая строка, желательно                       В терминах FSM, это название состояния,
                              следующая определённому соглашению             которое может принимать машина
                              (как вариант - приставка `in_` перед 
                              названием состояния)
``initial``     нет           "true", само наличие атрибута определяющее     Состояние, в которое машина переходит
                                                                             сразу же после запуска
``final``       нет           "true", само наличие атрибута определяющее     Индикатор конечного состояния машины
``targetns``    нет           Полный путь к модулю с callback`ами состояния. Используется для сокращения записей
                              Используется принятый в Python формат          об источнике callback`ов состояния
=============== ============= ============================================== ==========================================

Тег **<state>** может включать в себя:

* **<transition>** – описание возможных переходов в другие состояния ("входной алфавит" в терминах FSM или "список событий" в терминах HSME)
* **<onentry>** – callback, срабатывающий *при попытке войти* в состояние
* **<onchange>** – callback, срабатывающий *во время входа* в состояние
* **<onexit>** – callback, срабатывающий во время *попытки выхода* из состояния
* **<state>** – вложенное подсостояние, может встречаться 0 или более раз


<transition>
~~~~~~~~~~~~
Тег **<transition>** описывает атрибутами *event* и *next*, по какому событию `event` в какое состояние `next` можно перейти из текущего состояния.

.. code-block:: xml

    <transition event="do_goto_in_basket_freeze" next="in_recalculation"/>

Может встречаться 0 и более раз в описании состояния.


<onentry>
~~~~~~~~~
Тег **<onentry>** описывает атрибутом *target* имя функции callback`а на попытку входа в состояние. Значение *target* – полный путь к данной функции в python-стиле "пакет.модуль.функция". Если в определении *<state>* был указан атрибут *targetns*, путь к функции можно опустить. Таким образом, запись:

.. code-block:: xml

    <state id="in_basket_normal" targetns="charts.basket_callbacks.in_basket_normal">
        <onentry target="on_enter_in_basket_normal"/>
    </state>

и:

.. code-block:: xml

    <state id="in_basket_normal">
        <onentry target="charts.basket_callbacks.in_basket_normal.on_enter_in_basket_normal"/>
    </state>

абсолютно равнозначны.

.. note::

    Переход в состояние осуществляется только в случае успешной отработки логики *<onentry>*. Тег может быть указан только 1 раз в родительском *<state>*.


<onchange>
~~~~~~~~~~
Тег **<onchange>** описывает атрибутом *target* имя функции callback`а на состояние. Значение *target* – полный путь к данной функции в python-стиле "пакет.модуль.функция". Если в определении *<state>* был указан атрибут *targetns*, путь к функции можно опустить. Таким образом, запись:

.. code-block:: xml

    <state id="in_basket_normal" targetns="charts.basket_callbacks.in_basket_normal">
        <onchange target="on_change_in_basket_normal"/>
    </state>

и:

.. code-block:: xml

    <state id="in_basket_normal">
        <onchange target="charts.basket_callbacks.in_basket_normal.on_change_in_basket_normal"/>
    </state>

абсолютно равнозначны.

.. note::

    Тег может быть указан только 1 раз в родительском *<state>*.


<onexit>
~~~~~~~~~~
Тег **<onexit>** описывает атрибутом *target* имя функции callback`а на попытку выхода из состояния. Значение *target* – полный путь к данной функции в python-стиле "пакет.модуль.функция". Если в определении *<state>* был указан атрибут *targetns*, путь к функции можно опустить. Таким образом, запись:

.. code-block:: xml

    <state id="in_basket_normal" targetns="charts.basket_callbacks.in_basket_normal">
        <onexit target="on_exit_in_basket_normal"/>
    </state>

и:

.. code-block:: xml

    <state id="in_basket_normal">
        <onexit target="charts.basket_callbacks.in_basket_normal.on_exit_in_basket_normal"/>
    </state>

абсолютно равнозначны.

.. note::

    В случае неудачи отработки логики *<onexit>*, выхода из состояния не происходит. Тег может быть указан только 1 раз в родительском *<state>*.


<state>
~~~~~~~
Вложенные состояния могут использоваться для группировки по логическому принципу. Состояние, которое включает в себя вложенные состояния является мета-состоянием. Помимо структурной (визуальной) группировки на уровне описания, для meta-состояния создаётся набор служебных событий для переходов во вложенные состояния.

Для мета-состояния "in_recalculation", на этапе парсинга во внутреннее представление, создаются служебные события вида *do_goto_* + *имя_вложенного_состояния*. Записи вида:

.. code-block:: xml

    <state id="in_recalculation" targetns="charts.basket_callbacks.in_recalculation">
        <onentry target="on_enter_in_recalculation"/>
        <onchange target="on_change_in_recalculation"/>
        <onexit target="on_exit_in_recalculation"/>

        <state id="in_basket_normal" targetns="charts.basket_callbacks.in_basket_normal">
            <onentry target="on_enter_in_basket_normal"/>
            <onchange target="on_change_in_basket_normal"/>
            <onexit target="on_exit_in_basket_normal"/>

            <transition event="do_goto_in_basket_normal" next="in_recalculation"/>
            <transition event="do_add_to_basket" next="in_recalculation"/>
            <transition event="do_remove_product" next="in_recalculation"/>
        </state>

        <state id="in_basket_empty" initial="true">
            <transition event="do_add_to_basket" next="in_recalculation"/>
        </state>

    </state>

и:

.. code-block:: xml

    <state id="in_recalculation" targetns="charts.basket_callbacks.in_recalculation">
        <onentry target="on_enter_in_recalculation"/>
        <onchange target="on_change_in_recalculation"/>
        <onexit target="on_exit_in_recalculation"/>

        <transition event="do_goto_in_basket_normal" next="in_basket_normal"/>
        <transition event="do_goto_in_basket_empty" next="in_basket_empty"/>

    </state>

    <state id="in_basket_normal" targetns="charts.basket_callbacks.in_basket_normal">
        <onentry target="on_enter_in_basket_normal"/>
        <onchange target="on_change_in_basket_normal"/>
        <onexit target="on_exit_in_basket_normal"/>

        <transition event="do_goto_in_basket_normal" next="in_recalculation"/>
        <transition event="do_add_to_basket" next="in_recalculation"/>
        <transition event="do_remove_product" next="in_recalculation"/>
    </state>

    <state id="in_basket_empty" initial="true">
        <transition event="do_add_to_basket" next="in_recalculation"/>
    </state>

абсолютно равнозначны.


.. note::

    Callback`и и пространство имён callback`ов мета-состояния не распространяются на вложенные состояния. Описания тегов <onchange>, <onentry>, <onexit> и state-атрибута `targetns` не наследуются.
