# https://refactoring.guru/design-patterns/composite/python/example
from __future__ import annotations
from abc import ABC, abstractmethod

class Component(ABC):
    """
    The base Component class declares common operations for both simple and
    complex objects of a composition.
    """

    @property
    def parent(self) -> Component:
        return self._parent

    @parent.setter
    def parent(self, parent: Component):
        """
        Optionally, the base Component can declare an interface for setting and
        accessing a parent of the component in a tree structure. It can also
        provide some default implementation for these Methods.
        """

        self._parent = parent

    """
    In some cases, it would be beneficial to define the child-management
    operations right in the base Component class. This way, you won't need to
    expose any concrete component classes to the client code, even during the
    object tree assembly. The downside is that these Methods will be empty for
    the leaf-level components.
    """

    def add(self, component: Component) -> None:
        pass

    def remove(self, component: Component) -> None:
        pass

    def is_composite(self) -> bool:
        """
        You can provide a method that lets the client code figure out whether a
        component can bear children.
        """

        return False

    def getConf(self):
        pass

    def add_method(self, method):
        pass

    def remove_method(self, method):
        pass

    def getChild(self, name):
        pass

    def impModule(self, item):
        pass

    def instantiateObj(self, item, modules_conf):
        pass

    def learn(self):
        pass

    def process(self):
        pass
