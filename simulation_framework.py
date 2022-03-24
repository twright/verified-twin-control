from abc import ABCMeta, abstractmethod


class Simulator(metaclass=ABCMeta):
    @abstractmethod
    def run(self):
        raise NotImplementedException("Need to implement the run function")
        

class Model(Simulator):
    pass


class Controller(Simulator):
    pass