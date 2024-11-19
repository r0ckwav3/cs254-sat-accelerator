import pyrtl
import pathlib
import sys
import random

# slightly sketchy way to allow upward imports
directory = pathlib.Path(__file__)
sys.path.append(str(directory.parents[1]))

import helpers

def double_saturate_one_bit_test():
    pyrtl.reset_working_block()
    pyrtl.set_debug_mode(True)

    # setup
    in_1 = pyrtl.Input(bitwidth=1, name="double_saturate_one_bit_test_in_1")
    in_2 = pyrtl.Input(bitwidth=1, name="double_saturate_one_bit_test_in_2")
    out = pyrtl.Output(bitwidth=2, name="double_saturate_one_bit_test_out")
    out <<= helpers.double_saturate(in_1, in_2)

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
    out <<= helpers.double_saturate(in_1, in_2)

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

def create_bin_tree_add_test():
    pyrtl.reset_working_block()
    pyrtl.set_debug_mode(True)

    # setup
    in_count = 11
    ins = [
        pyrtl.Input(bitwidth=10, name=f"create_bin_tree_add_test_in_{i}")
        for i in range(in_count)
    ]
    out = pyrtl.Output(bitwidth=10, name="create_bin_tree_add_test_out")
    op = lambda a,b: a+b
    out <<= helpers.create_bin_tree(ins, op)

    # test
    sim_trace = pyrtl.SimulationTrace()
    sim = pyrtl.Simulation(tracer=sim_trace)

    random.seed(77777)
    for i in range(100):
        nums = [random.randint(0,1023) for i in range(in_count)]
        expected = sum(nums) % 1024
        in_state = {
            f"create_bin_tree_add_test_in_{i}": nums[i] for i in range(in_count)
        }

        sim.step(in_state)
        assert sim_trace.trace["create_bin_tree_add_test_out"][-1] == expected

tests = [
    double_saturate_one_bit_test,
    double_saturate_two_bit_test,
    create_bin_tree_add_test
]

if __name__ == "__main__":
    for test in tests:
        print("Running", test.__name__)
        test()

# note this doesn't acutally work down here, you need to put it into a dunction before the asserts that are breaking
# sim_trace.render_trace()
