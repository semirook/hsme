# coding: utf-8
import random


class Product(object):

    def __init__(self, id, name=None):
        self.id = id
        self.name = name
        self.is_available = True
        self.is_reserved = False
        self.cost = 50

    @classmethod
    def produce_normal(cls, id=None):
        product = cls(id or random.randint(1, 1000))
        return product

    @classmethod
    def produce_unavailable(cls, id=None):
        product = cls.produce_normal(id)
        product.is_available = False
        return product


class Basket(object):

    def __init__(self):
        self.products = []

    def __iter__(self):
        return iter(self.products)

    def add(self, product):
        self.products.append(product)

    def remove(self, product):
        self.products.remove(product)

    @property
    def amount(self):
        return len(self.products)

    def total_cost(self):
        return sum(p.cost for p in self.products)

    def same_product_count(self, product):
        return sum(1 if p == product else 0 for p in self.products)


class DataStore(object):

    def __init__(self):
        self.users = {}
        self.products = {}

    def get_user(self, user_id):
        return self.users.get(user_id)

    def add_user(self, user):
        self.users[user.id] = user

    def get_product(self, product_id):
        return self.products.get(product_id)

    def add_product(self, product):
        self.products[product.id] = product


class User(object):

    def __init__(self, id):
        self.id = id
        self.role = None
        self.state_machines = {}

    @classmethod
    def produce_normal(cls, id=None):
        user = cls(id or random.randint(1, 1000))
        user.role = 'normal'
        return user

    @classmethod
    def produce_stuff(cls, id=None):
        user = cls.produce_normal(id)
        user.role = 'stuff'
        return user

    @classmethod
    def produce_banned(cls, id=None):
        user = cls.produce_normal(id)
        user.role = 'banned'
        return user

    def is_banned(self):
        return self.role == 'banned'

    def get_state_machine(self, sm_type):
        return self.state_machines.get(sm_type)

    def add_state_machine(self, sm_type, sm_pickle):
        self.state_machines[sm_type] = sm_pickle
