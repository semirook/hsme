# coding=utf-8
import unittest
from fsm.parsers import HSMEDictsParser
from fsm.helpers import HSMERunnerMK, HSMERunnerFactory
from .charts.checkout import SIMPLE_CHECKOUT


class SimpleHelpersTests(unittest.TestCase):

    def test_factory(self):
        factory = HSMERunnerFactory(HSMERunnerMK, 3)
        self.assertTrue(len(factory.runners) == 3)
        for runner in factory.runners:
            self.assertIsInstance(runner, HSMERunnerMK)

    def test_api(self):
        factory = HSMERunnerFactory(HSMERunnerMK, 3)
        hsme_1 = factory.get_free()
        checkout_sm = HSMEDictsParser(
            SIMPLE_CHECKOUT, 'checkout',
            datamodel={
                'USER_ID': 1,
                'SM_NAME': 'checkout',
            }
        ).parse()
        hsme_1.load(checkout_sm, autosave=False)

        hsme_2 = factory.get_free()
        checkout_sm = HSMEDictsParser(
            SIMPLE_CHECKOUT, 'checkout',
            datamodel={
                'USER_ID': 2,
                'SM_NAME': 'checkout',
            }
        ).parse()
        hsme_2.load(checkout_sm, autosave=False)

        hsme = factory.get_current(user_id=1, sm_name='checkout')
        self.assertEqual(hsme, hsme_1)

        hsme = factory.get_current(user_id=2, sm_name='checkout')
        self.assertEqual(hsme, hsme_2)

        hsme = factory.get_current(user_id=3, sm_name='checkout')
        self.assertIsNone(hsme)

        some_hsme = factory.get_not_ids(user_id=1, sm_name='checkout')
        self.assertNotEqual(some_hsme, hsme_1)

        self.assertTrue(hsme_1.is_occupied_by(user_id=1))
