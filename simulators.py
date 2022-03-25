from sage.all import RIF, RR, QQ
import sage.all as sg
from scipy.integrate import solve_ivp

from .simulation_framework import Simulator


class VerifiedContinuousSimulator(Simulator):
    def __init__(self, state, model):
        self.state = state
        self.model = model
        
    def run(self, time_limit=RIF("Inf"), time_step=RIF("Inf")):
        # Model state
        t = RIF("0")
        x = None
        
        gen = self.model.run()
        
        while t.lower() < time_limit.lower():
            run_duration = RIF(min(time_step.lower(), (time_limit - t).lower()), min(time_step.upper(), (time_limit - t).upper()))
            
            x = next(gen)
            yield gen.send((time_step, x, self.state))
            
            t = t + run_duration
            

class NumericalContinuousSimulator(Simulator):
    def __init__(self, state, model):
        self.state = state
        self.model = model
        
    def run(self, time_limit=RR("Inf"), time_step=RR("Inf")):
        # Model state
        t = QQ(0)
        x = None
        
        gen = self.model.run()
        
        while t < time_limit:
            run_duration = min(time_step, (time_limit - t))
            print(f"run_duration = {run_duration}")
                        
            x = next(gen)
            yield gen.send((run_duration, x, self.state))
            
            t = t + run_duration
            
            
class DiscreteSimulator:
    def __init__(self, x, controller):
        self.x = x
        self.controller = controller
        
    def run(self):
        controller_gen = self.controller.run()
        
        yield (state := next(controller_gen))
        
        while True:
            controller_gen.send(self.x)
            _, _, state = next(controller_gen)
            yield state
            
            
class HybridSimulator:
    def __init__(self, model, controller, controller_input_map=None, controller_output_map=None):
        self.model = model
        self.controller = controller
        # Transfrom model state for input into controller
        self.controller_input_map = (controller_input_map
                                     if controller_input_map is not None
                                     else (lambda x: x))
        # Generate new model state based on original model state and 
        # controller output (e.g. embed controller output in state)
        # vector
        self.controller_output_map = (controller_output_map
                                      if controller_output_map is not None
                                      else (lambda xin, x: x))
        
    def run(self, time_limit=RIF('Inf'), time_step=RIF('Inf')):
        # Model state
        t = RIF("0")
        
        model_gen = self.model.run()
        controller_gen = self.controller.run()
        
        yield (state := next(controller_gen))
        
        # Use a suitable lower time limit for minimum simulation time to avoid failure
        # or loops at the end
        while 1e-5 <= time_limit.lower() - t.lower():
            xin = x = next(model_gen)
            next(controller_gen)
            trun, x, state = controller_gen.send(self.controller_input_map(x))
            yield state
            run_duration = RIF(min(trun.lower(), time_step.lower(), (time_limit - t).lower()),
                               min(trun.upper(), time_step.upper(), (time_limit - t).upper()))
            yield model_gen.send((run_duration, self.controller_output_map(xin, x), state))
            
            t = t + run_duration