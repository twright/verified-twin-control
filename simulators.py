from sage.all import RIF

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
    def __init__(self, model, controller):
        self.model = model
        self.controller = controller
        
    def run(self, time_limit=RIF('Inf'), time_step=RIF('Inf')):
        # Model state
        t = RIF("0")
        
        model_gen = self.model.run()
        controller_gen = self.controller.run()
        
        yield (state := next(controller_gen))
        
        # Use a suitable lower time limit for minimum simulation time to avoid failure
        # or loops at the end
        while 1e-5 <= time_limit.lower() - t.lower():
            x = next(model_gen)
            next(controller_gen)
            trun, x, state = controller_gen.send(x)
            yield state
            run_duration = RIF(min(trun.lower(), time_step.lower(), (time_limit - t).lower()),
                               min(trun.upper(), time_step.upper(), (time_limit - t).upper()))
            yield model_gen.send((run_duration, x, state))
            
            t = t + run_duration