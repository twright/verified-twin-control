from sage.all import RIF

from enum import Enum, auto

from .simulation_framework import Controller


class BasicController(Controller):
    def __init__(self, initial_state):
        self.initial_state = initial_state
    
    def control_step(self, x, state):
        raise NotImplementedError("Control step needs to be implemented")
    
    def run_iter(self):
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

 
class SignalFnSwitchedController(BasicController):
    def __init__(self, initial_state, input_signals_fns: dict):
        self.input_signals_fns = input_signals_fns
        super().__init__(initial_state)
    
    def control_step(self, t, state):
        output_state = dict(**state)
        # run_duration = RIF("Inf")
        for k, sig_fn in self.input_signals_fns.items():
            # Potentially unsafe: we only look at midpoint of time interval
            output_state[k] = sig_fn(t.midpoint())
        
        # No good way at the moment to detect next time of signal value
        # change so we rely on being given a fixed step size
        return (RIF('Inf'), t, output_state)


class SignalArraySwitchedController(BasicController):
    def __init__(self, initial_state, timepoints, input_signals_arrays: dict):
        self.timepoints = timepoints
        self.input_signals_arrays = input_signals_arrays
        super().__init__(initial_state)

    @staticmethod
    def next_signal_change(t0, v0, ts, vs):
        for (t, v) in zip(ts, vs):
            if t >= t0 and v != v0:
                return t, v

        return None

    @staticmethod
    def current_signal_state(t0, v0, ts, vs):
        v_current = v0

        for (t, v) in zip(ts, vs):
            if t > t0:
                break

            v_current = v

        return v_current


    def next_state_update(self, state, t0):
        next_changes = sorted(
            filter(
                (lambda x: x[1] is not None),
                (
                    (k, self.next_signal_change(t0, state[k], self.timepoints, sig_arr))
                    for k, sig_arr
                    in self.input_signals_arrays.items()
                )
            ),
            key=(lambda x: -x[1][0]),
        )

        try:
            return next_changes[0]
        except IndexError:
            return None
    
    def control_step(self, t, state):
        run_duration = RIF("Inf")

        output_state = dict(**state)

        for k, sig_arr in self.input_signals_arrays.items():
            output_state[k] = self.current_signal_state(t.upper(), state[k],
                self.timepoints, sig_arr)
        
        state_change = self.next_state_update(output_state, t.upper())
        if state_change is not None:
            k, (t_next, v_new) = state_change  # type: ignore
            return (RIF(t_next) - t, t, output_state)
        else:
            return (RIF('Inf'), t, output_state)


class OpenLoopState(Enum):
    INITIALIZED = auto()
    HEATING = auto()
    COOLING = auto()
    FIRST = auto()


class PeriodicOpenLoopController(BasicController):
    def __init__(self, step_size, n_samples_period: int, n_samples_heating: int):
        assert n_samples_heating >= 0
        self.step_size = RIF(step_size)
        self.n_samples_period = n_samples_period
        self.n_samples_heating = n_samples_heating
        super().__init__({
            'heater_on': False,
            'current_state': OpenLoopState.FIRST,
        })

    def control_step(self, t, state):
        new_state = dict(**state)
        next_delay = None

        if state['current_state'] == OpenLoopState.FIRST:
            next_delay = RIF("0")
            new_state['current_state'] = OpenLoopState.INITIALIZED
        elif state['current_state'] == OpenLoopState.INITIALIZED:
            new_state['heater_on'] = False
            if self.n_samples_heating > 0:
                # Why do these values work?
                next_delay = 2*RIF(self.step_size)
                new_state['current_state'] = OpenLoopState.HEATING
                # next_delay = RIF(self.n_samples_heating)*self.step_size
            else:
                assert self.n_samples_heating == 0
                new_state['current_state'] = OpenLoopState.COOLING
                next_delay = RIF("Inf") # RIF(self.n_samples_period - self.n_samples_heating)*self.step_size
        # if state['current_state'] == OpenLoopState.INITIALIZED:
        #     new_state['heater_on'] = False
        #     if self.n_samples_heating > 0:
        #         new_state['current_state'] = OpenLoopState.HEATING
        #         next_delay = RIF(self.n_samples_heating)*self.step_size
        #         # new_state['current_state'] = OpenLoopState.COOLING
        #         # next_delay = RIF(self.n_samples_period - self.n_samples_heating)*self.step_size
        #     else:
        #         assert self.n_samples_heating == 0
        #         new_state['current_state'] = OpenLoopState.COOLING
        #         next_delay = RIF("Inf") # RIF(self.n_samples_period - self.n_samples_heating)*self.step_size
        elif state['current_state'] == OpenLoopState.HEATING:
            new_state['heater_on'] = True
            new_state['current_state'] = OpenLoopState.COOLING
            next_delay = RIF(self.n_samples_period - self.n_samples_heating)*self.step_size
        elif state['current_state'] == OpenLoopState.COOLING:
            new_state['heater_on'] = False
            new_state['current_state'] = OpenLoopState.HEATING
            next_delay = RIF(self.n_samples_heating)*self.step_size
        else:
            assert False

        return next_delay, t, new_state

