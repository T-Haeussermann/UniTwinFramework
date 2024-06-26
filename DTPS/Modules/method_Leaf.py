from Modules.class_ComponentABC import Component

class method_Leaf(Component):
    def __init__(self):
        self._id = "method_Leaf"
        self._subscribers = {}
        self.parent = ""
    def method_Leaf(self):
        print(self.__dict__)
        print("Leaf geht!")