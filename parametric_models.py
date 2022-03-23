from .base import *

import lbuc

from sage.symbolic.function_factory import function_factory


class ParametricModel(lbuc.System):
    def __init__(self, vs : str, T0s : list, Ts : list, params : dict):
        RR = sg.PolynomialRing(RIF, vs)
        self.vs = vs.split(',')
        self.Ts = Ts
        self.T0s = T0s
        self.params = params
        TsRR = [RR(T.subs(**params)) for T in Ts]
        super().__init__(RR, RR.gens(), T0s, TsRR)
    
    @property
    def fns(self):
        return [
            function_factory(v, 1)(t) for v in self.vs
        ]
    
    @property
    def fnmap(self):
        return {
            v: fn for (v, fn) in zip(self.vs, self.fns)
        }
    
    @property
    def odes(self):
        return [
            sg.diff(fn, t) == T.subs(**self.fnmap)
                for (fn, T) in zip(self.fns, self.Ts)
        ]
    
    @property
    def ode_table(self):
        return sg.table([[ode] for ode in self.odes])


