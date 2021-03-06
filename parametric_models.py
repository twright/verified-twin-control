from .base import *
from sage.all import RR, QQ
import sage.all as sg
from scipy.integrate import solve_ivp
from sage.symbolic.function_factory import function_factory

import lbuc

from .simulation_framework import Model
from .traces import VerifiedContinuousTrace, NumericalContinuousTrace


class ParametricModel(lbuc.System, Model):
    BaseField = None
    
    def __init__(self, vs : str, T0s : list, Ts : list, params : dict, nonpoly=False, vars=None):
        if nonpoly:
            R = sg.SR
        else:
            R = sg.PolynomialRing(self.BaseField, vs)
            vars = R.gens()
        self.nonpoly = nonpoly
        self.vs = vs.split(',')
        self.Ts = Ts
        self.T0s = T0s
        self.params = params
        TsRR = [R(T.subs(**params)) for T in Ts]
        super().__init__(R, vars, T0s, TsRR)
        
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


    
class IntervalParametricModel(ParametricModel):
    """A LBUC System defined based on a parametric set of ODEs."""
    BaseField = RIF
    
    def run_iter(self):
        x = self.T0s
        trun = RIF('0')
        
        while True:
            # State does not matter
            trun, x, _ = (yield x)
            # print(f"running for {trun.str(style='brackets')} ...")
            # Take one continuous reachability step
            reach = self.reach(trun,
                integration_method=(lbuc.IntegrationMethod.NONPOLY_TAYLOR
                    if self.nonpoly
                    else lbuc.IntegrationMethod.LOW_DEGREE))
            yield reach
            x = reach(trun)

    @property
    def TraceType(cls):
        return VerifiedContinuousTrace

            
class NumericalParametricModel(ParametricModel):
    """A LBUC System defined based on a parametric set of ODEs."""
    BaseField = QQ
    
    def run_iter(self):
        x = self.y0
        trun = QQ(0)
        
        odes = sg.vector(self.y)
        # print(f"odes = {odes}")
        R = self.R
        f = lbuc.vec_to_numpy(R, odes)
        jac = lbuc.mat_to_numpy(R, sg.jacobian(odes, R.gens()))
        
        while True:
            # State does not matter
            trun, x, _ = (yield x)
            print(f"running for {trun} ...")
            # Compute numerical solution for one step
            print(f"x = {x}")
            sln = solve_ivp(
                f,
                (0, trun),
                x,
                method='LSODA',
                jac=jac,
                vectorized=True,
                dense_output=True,
            )
            yield sln
            x = sln.sol(trun)

    @property
    def TraceType(cls):
        return NumericalContinuousTrace
            

class SwitchingParametricModel(Model):
    """A model which switches between multiple different parametric models based on the values of different state 
       variables."""
    
    def __init__(self, x0, **params):
        self.x0 = x0
        self.BaseField = x0[0].base_ring()
        self.params = params
        
    def model_fn(self, x, state):
        raise NotImplementedError()
                
    def run_iter(self):
        x = self.x0
        trun = self.BaseField(0)
        
        while True:
            trun, x, state = (yield x)
            trun = self.BaseField(trun)
            # Take one continuous reachability step
            gen = self.model_fn(x, state).run_iter()
            next(gen)
            yield (res := gen.send((trun, x, state)))
            x = res(trun)

    @property
    def TraceType(self):
        return (VerifiedContinuousTrace
                if self.BaseField is RIF
                else NumericalContinuousTrace)