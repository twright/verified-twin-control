from .base import *

import lbuc

from .simulation_framework import Model

from sage.symbolic.function_factory import function_factory


class ParametricModel(lbuc.System, Model):
    """A LBUC System defined based on a parametric set of ODEs."""
    
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
    
    def run(self):
        x = self.x0
        trun = RIF('0')
        
        while True:
            # State does not matter
            trun, x, _ = (yield x)
            print(f"running for {trun.str(style='brackets')} ...")
            # Take one continuous reachability step
            reach = self.reach(trun)
            yield reach
            x = reach(trun)


class SwitchingParametricModel(Model):
    """A model which switches between multiple different parametric models based on the values of different state 
       variables."""
    
    def __init__(self, x0):
        self.x0 = x0
        
    def model_fn(self, x, state):
        raise NotImplementedException()
                
    def run(self):
        x = self.x0
        trun = RIF("0")
        
        while True:
            trun, x, state = (yield x)
            print(f"running for {trun.str(style='brackets')} ...")
            # Take one continuous reachability step
            reach = self.model_fn(x, state).reach(trun)
            yield reach
            x = reach(trun)