from abc import ABCMeta, abstractclassmethod, abstractmethod, abstractproperty

from sage.all import RIF

from .traces import Trace, DiscreteTrace, ContinuousTrace

class Simulator(metaclass=ABCMeta):
    @abstractmethod
    def run_iter(self):
        raise NotImplementedError("Need to implement the run_iter function")

    @abstractmethod
    def run(self) -> Trace:
        raise NotImplementedError("Need to implement the run function")

    @abstractproperty
    def TraceType(self):
        raise NotImplementedError()


class Model(Simulator):
    def run(self) -> ContinuousTrace:
        return self.TraceType(RIF("[0, Inf]"), self.run_iter())


class Controller(Simulator):
    @property
    def TraceType(self):
        return DiscreteTrace

    def run(self):
        return DiscreteTrace(self.run_iter())