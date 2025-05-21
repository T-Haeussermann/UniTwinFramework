from .class_ComponentABC import Component
from .class_ConfigStorage import class_ConfigStorage
from .class_Composite import Composite



class Composite_Standalone(Composite):

    def __int__(self, conf):
        self._conf = conf

    def getConf(self):
        pass

    def learn(self):
        return "Not available in standalone mode."
