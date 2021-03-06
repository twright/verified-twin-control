import abc
from typing import Any, Dict, List, Optional, Union, Iterable, Tuple
from typing_extensions import TypeAlias
from functools import partial

from scipy.integrate import OdeSolution
from sage.all import RIF
import sage.all as sg

import lbuc


"""Classes representing traces produced by discrete simulation and continuous or hybrid verified integration."""

DiscreteState: TypeAlias = Dict
ContinuousState: TypeAlias = lbuc.Reach
NumericalState: TypeAlias = OdeSolution
VerifiedHybridState: TypeAlias = Union[DiscreteState, ContinuousState]
NumericalHybridState: TypeAlias = Union[DiscreteState, NumericalState]


class Trace(metaclass=abc.ABCMeta):
    def __init__(self, values: Iterable[Any]):
        self._values : List[Any] = list(values)

    def __iter__(self):
        yield from self._values

    @property
    def values(self):
        return self._values


class DiscreteTrace(Trace):
    def __init__(self, values: Iterable):
        assert all(isinstance(v, dict) for v in values)


class RealTimeTrace(Trace, metaclass=abc.ABCMeta):
    def __init__(self, domain: RIF, values):
        self._domain = domain
        super().__init__(values)

    @property
    def domain(self) -> RIF:
        return self._domain

    @property
    def time(self) -> RIF:
        return self.domain.upper()

    def __call__(self, t) -> Any:
        raise NotImplementedError()

    @abc.abstractmethod
    def plot(self, variables: Tuple[Any], **kwargs) -> 'sg.Graphics':
        raise NotImplementedError()


class ContinuousTrace(RealTimeTrace, metaclass=abc.ABCMeta):
    pass


class VerifiedContinuousTrace(ContinuousTrace):
    def __init__(self, domain: RIF, values: Iterable[ContinuousState]):
        values = list(values)
        assert all(isinstance(v, lbuc.Reach) for v in values)
        super().__init__(domain, values)

    def plot(self, variables: Tuple[str], **kwargs) -> 'sg.Graphics':
        # Add extra plotting arguments
        if 'step' not in kwargs:
            kwargs['step'] = 0.5
        if 'straight' not in kwargs:
            kwargs['straight'] = True
        if 'joins' not in kwargs:
            kwargs['joins'] = False
        colors = kwargs.pop('color', ['blue']*len(variables))

        # Generate sage plot object
        return sum(
            (
                sum(r.sage_tube_plot('t', v, color=col, **kwargs)
                    for v, col in zip(variables, colors))
                for r in self
            ),
            sg.Graphics(),
        )
        # type: ignore

    @staticmethod
    def interval_list_union(xs, ys):
        if not xs:
            return ys
        if not ys:
            return xs
        return [x.union(y) for x, y in zip(xs, ys)]

    def __call__(self, t) -> RIF:
        y = None
        t0 = self.domain.edges()[0]
        
        for r in self.values:
            print(f"")
            if t.overlaps(t0 + RIF(0, r.time)): 
                y = self.interval_list_union(r(t - t0), y)
            t0 += RIF(r.time)

        return y


class NumericalContinuousTrace(ContinuousTrace):
    def __init__(self, domain: RIF, values: Iterable[NumericalState]):
        values = list(values)
        # assert all(isinstance(v, OdeSolution) for v in values)
        super().__init__(domain, values)

    def plot(self, variables: Tuple[int], **kwargs) -> 'sg.Graphics':
        var_fn = lambda r, i, t: r.sol(t - self.domain.lower())[i]

        return sum(
            (
                sg.plot(
                    tuple(partial(var_fn, r, i) for i in variables),
                    (self.domain.lower(), self.domain.upper()),
                    **kwargs,
                ) for r in self
            ),
            sg.Graphics(),
        )

    def __call__(self, t) -> Optional[float]:
        if t not in self.domain:
            return None

        for sol in self.values:
            y = sol.sol(t)
            if y is not None:
                return y
        
        return None


class HybridTrace(RealTimeTrace):
    @abc.abstractproperty
    def continuous_part(self) -> ContinuousTrace:
        raise NotImplementedError()

    @property
    def discrete_part(self) -> DiscreteTrace:
        return DiscreteTrace(v for v in self if isinstance(v, dict))

    def plot(self, variables: Tuple[str], **kwargs) -> 'sg.Graphics':
        return self.continuous_part.plot(variables, **kwargs)

    def __call__(self, t) -> Any:
        return self.continuous_part(t)


class VerifiedHybridTrace(HybridTrace):
    def __init__(self, domain: RIF, values: Iterable[VerifiedHybridState]):
        values = list(values)
        assert all(isinstance(v, (lbuc.Reach, dict)) for v in values)
        super().__init__(domain, values)

    @property
    def continuous_part(self) -> VerifiedContinuousTrace:
        return VerifiedContinuousTrace(
            self.domain,
            (v for v in self if isinstance(v, lbuc.Reach)),
        )


class NumericalHybridTrace(HybridTrace):
    def __init__(self, domain: RIF, values: Iterable[NumericalHybridState]):
        values = list(values)
        assert all(isinstance(v, (OdeSolution, dict)) for v in values)
        super().__init__(domain, values)

    @property
    def continuous_part(self) -> NumericalContinuousTrace:
        return NumericalContinuousTrace(
            self.domain,
            (v for v in self if isinstance(v, OdeSolution)),
        )