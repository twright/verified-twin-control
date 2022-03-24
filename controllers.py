from sage.all import RIF

from .simulation_framework import Controller


class BasicController(Controller):
    def __init__(self, initial_state):
        self.initial_state = initial_state
    
    def control_step(self, x, state):
        raise NotImplementedException("Control step needs to be implemented")
    
    def run(self):
        x = None
        state = self.initial_state
        
        yield state
        
        while True:
            x = (yield)
            trun, x, state = self.control_step(x, state)
            yield (trun, x, state)


class TrivialController(BasicController):    
    def control_step(self, x, state):
        return RIF("Inf"), x, state
    
    
class SignalSwitchedController(BasicController):
    def __init__(self, initial_state, input_signals: dict):
        self.input_signals = input_signals
        super().__init__(initial_state)
    
    def control_step(self, x, state):
        t = x[0]
        
        output_state = dict(**state)
        run_duration = RIF("Inf")
        for k, s in self.input_signals.items():
            try:
                # FIXME: dirty hack to find the edge of the domain which the current timepoint belongs in
                current_domain, output_state[k] = next((d, v) for d, v in s.values if (t+RIF("0.5")).overlaps(d))
            except StopIteration:
                current_domain, output_state[k] = s.values[-1]
            run_duration = min(run_duration, current_domain.edges()[1] - t)
        
        return (run_duration, x, output_state)