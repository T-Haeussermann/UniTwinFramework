# class Event(object):
#
#     def __init__(self):
#         self.__eventhandlers = []
#
#     def __iadd__(self, handler):
#         self.__eventhandlers.append(handler)
#         return self
#
#     def __isub__(self, handler):
#         self.__eventhandlers.remove(handler)
#         return self
#
#     def __call__(self, *args, **keywargs):
#         for eventhandler in self.__eventhandlers:
#             eventhandler(*args, **keywargs)

class Event(object):

    def __init__(self):
        self.__eventhandlers = {}

    def __iadd__(self, handlers_dict):
        for identifier, handler in handlers_dict.items():
            if callable(handler):
                self.__eventhandlers[identifier] = handler
        print(self.__eventhandlers)
        return self

    def __isub__(self, identifier):
        if identifier in self.__eventhandlers:
            del self.__eventhandlers[identifier]
        return self

    def __call__(self, *args, **kwargs):
        for eventhandler in self.__eventhandlers.values():
            eventhandler(*args, **kwargs)

