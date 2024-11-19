import pyrtl
import pathlib
import sys

# slightly sketchy way to allow upward imports
directory = pathlib.Path(__file__)
sys.path.append(str(directory.parents[1]))

from bcp.helpers import *

def double_saturate_one_bit_test():
    pyrtl.reset_working_block()
    pyrtl.set_debug_mode(True)

    # setup
    in_1 = pyrtl.Input(bitwidth=1, name="double_saturate_one_bit_test_in_1")
    in_2 = pyrtl.Input(bitwidth=1, name="double_saturate_one_bit_test_in_2")
    out = pyrtl.Output(bitwidth=2, name="double_saturate_one_bit_test_out")
    out <<= double_saturate(in_1, in_2)

    # test
    sim_trace = pyrtl.SimulationTrace()
    sim = pyrtl.Simulation(tracer=sim_trace)

    test_vals = [
        [0,0,0],
        [0,1,1],
        [1,0,1],
        [1,1,3],
    ]

    for tv in test_vals:
        sim.step({"double_saturate_one_bit_test_in_1": tv[0], "double_saturate_one_bit_test_in_2": tv[1]})
        assert sim_trace.trace["double_saturate_one_bit_test_out"][-1] == tv[2]

def double_saturate_two_bit_test():
    pyrtl.reset_working_block()
    pyrtl.set_debug_mode(True)

    # setup
    in_1 = pyrtl.Input(bitwidth=2, name="double_saturate_two_bit_test_in_1")
    in_2 = pyrtl.Input(bitwidth=2, name="double_saturate_two_bit_test_in_2")
    out = pyrtl.Output(bitwidth=2, name="double_saturate_two_bit_test_out")
    out <<= double_saturate(in_1, in_2)

    # test
    sim_trace = pyrtl.SimulationTrace()
    sim = pyrtl.Simulation(tracer=sim_trace)

    test_vals = [
        [0,0,0],
        [0,1,1],
        [0,3,3],
        [1,0,1],
        [1,1,3],
        [1,3,3],
        [3,0,3],
        [3,1,3],
        [3,3,3],
    ]

    for tv in test_vals:
        sim.step({"double_saturate_two_bit_test_in_1": tv[0], "double_saturate_two_bit_test_in_2": tv[1]})
        assert sim_trace.trace["double_saturate_two_bit_test_out"][-1] == tv[2]


tests = [
    double_saturate_one_bit_test,
    double_saturate_two_bit_test
]

if __name__ == "__main__":
    for test in tests:
        test()
