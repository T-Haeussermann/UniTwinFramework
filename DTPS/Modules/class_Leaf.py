from .class_ComponentABC import Component
from .class_Event import Event

class class_Leaf(Component):
    """
    The Leaf class represents the end objects of a composition. A leaf can't
    have any children.

    Usually, it's the Leaf objects that do the actual work, whereas Composite
    objects only delegate to their sub-components.
    """

    def __init__(self):
        self._id = "class_Leaf"
        self._subscribers = {}
        self.parent = ""
        self._event = Event()

    def operation(self) -> str:
        self._event()
        return self._id

    def display(self, input):
        print(input)
        self._event()