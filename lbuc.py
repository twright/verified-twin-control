import lbuc
from lbuc import *
# We are going to redefine atomic propositions
del globals()['Atomic']

from .traces import HybridTrace, VerifiedContinuousTrace


class Atomic(lbuc.Atomic):
    '''Extend Atomic in order to allow monitoring over continuous and hybrid
    traces.'''

    def signal(self, trace, *args, **kwargs):
        # We just have a single reach sequence
        if isinstance(trace, Reach):
            return super().signal(trace, *args, **kwargs)
        
        # We have a full hybrid trace and want to monitor the continuous part
        if isinstance(trace, HybridTrace):
            trace = trace.continuous_part
        
        # We currently need a continuous trace for monitoring at this stage 
        assert isinstance(trace, VerifiedContinuousTrace)

        # Generate the overall signal
        sigs = []
        start_time = trace.domain.edges()[0]
        for r in trace:
            sig = super().signal(r, symbolic_composition=True)
            sigs.append(sig.G(-start_time.edges()[0]))
            start_time += sig.domain.edges()[1]

        return reduce(Signal.union, sigs, Signal(trace.domain, []))