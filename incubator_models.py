"""The collection of incubator models to different degrees of precision."""

from .base import *

from .parametric_models import IntervalParametricModel, SwitchingParametricModel

from sage.all import var
from sage.all import RIF


var("T_S, T_H, T_A, T_F, C_S, C_H, C_A, C_F, I, T_R, G_S, G_H, G_B, G_F, V")


twopincubator = IntervalParametricModel(
    "T_S",
    [RIF("[20.0, 20.05]")],
    [(1/C_S)*(V*I - G_B*(T_S - T_R))],
    {
        "C_S": RIF("700.0"),
        "V":   RIF("0.03"),
        "I":   RIF("1.0"),
        "T_R": RIF("18.0"),
        "G_B": RIF("1.0"),
    }
)


fourpincubator = IntervalParametricModel(
    "T_H,T_A",
    [RIF("[21.0, 21.05]"), RIF("25.0")],
    [
        (1/C_H)*(V*I - G_H*(T_H - T_A)),
        (1/C_A)*(G_H*(T_H - T_A) - G_B*(T_A - T_R)),
    ],
    {
        "C_H": RIF("243.45802367"),
        "C_A": RIF("68.20829072"),
        "V":   RIF("12.00"),
        "I":   RIF("10.45"),
        "T_R": RIF("18.0"),
        "G_H": RIF("0.87095429"),
        "G_B": RIF("0.73572788"),
    },
)


sevenpincubator = IntervalParametricModel(
    "T_H,T_A,T_F",
    [RIF("[20.0, 20.05]"), RIF("20.0"), RIF("20.0")],
    [
        (1/C_H)*(V*I - G_H*(T_H - T_A)),
        (1/C_A)*(G_H*(T_H - T_A) - G_B*(T_A - T_R) - G_F*(T_A - T_F)),
        (1/C_F)*G_F*(T_F - T_A),
    ],
    {
        "C_H": RIF("700.0"),
        "C_A": RIF("700.0"),
        "C_F": RIF("700.0"),
        "V":   RIF("0.03"),
        "I":   RIF("1.0"),
        "T_R": RIF("18.0"),
        "G_H": RIF("1.0"),
        "G_B": RIF("1.0"),
        "G_F": RIF("1.0"),
    },
)


class SwitchingFourParameterModel(SwitchingParametricModel):
    def model_fn(self, x, state):
        return IntervalParametricModel(
            "t,T_H,T_A",
            x,
            [
                RIF(1),
                (RIF(1)/C_H)*(int(state['heater_on'])*V*I - G_H*(T_H - T_A)),
                (RIF(1)/C_A)*(G_H*(T_H - T_A) - G_B*(T_A - T_R)),
            ],
            {
                "C_H": RIF("243.45802367"),
                "C_A": RIF("68.20829072"),
                "V":   RIF("12.00"),
                "I":   RIF("10.45"),
                "T_R": RIF("21.25"),
                "G_H": RIF("0.87095429"),
                "G_B": RIF("0.73572788"),
            }
        )