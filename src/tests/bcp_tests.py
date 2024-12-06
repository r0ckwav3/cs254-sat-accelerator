import pyrtl
from pyrtl import Input, Output
import pathlib
import sys
import copy
import itertools

# slightly sketchy way to allow upward imports
directory = pathlib.Path(__file__)
sys.path.append(str(directory.parents[1]))

from bcp import BCP
from helpers import connect_wire_lists, wirevector_list

def basic_setup():
    bcp = BCP(8, 8, 4)
    bcp.start_i <<= Input(bitwidth = 1, name = "start")

    connect_wire_lists(bcp.var_vals_i,     wirevector_list(1, "var_vals", 4, Input))
    connect_wire_lists(bcp.var_assigned_i, wirevector_list(1, "var_assigned", 4, Input))

    active = Output(bitwidth = 1, name = "test_active")
    status = Output(bitwidth = 1, name = "status")
    va_addrs = wirevector_list(8, "va_addrs", 4, Output)
    va_write_addr = Output(bitwidth = 8, name = "va_write_addr")
    va_write_val = Output(bitwidth = 1, name = "va_write_val")
    va_write_enable = Output(bitwidth = 1, name = "va_write_enable")

    active <<= bcp.active_o
    status <<= bcp.status_o
    connect_wire_lists(va_addrs, bcp.va_addrs_o)
    va_write_addr <<= bcp.va_write_addr_o
    va_write_val <<= bcp.va_write_val_o
    va_write_enable <<= bcp.va_write_enable_o

    return bcp

DEFAULT_INPUT = {
    "start": 0,
    "var_vals_0": 0,
    "var_vals_1": 0,
    "var_vals_2": 0,
    "var_vals_3": 0,
    "var_assigned_0": 0,
    "var_assigned_1": 0,
    "var_assigned_2": 0,
    "var_assigned_3": 0,
}

def bcp_inactive_test():
    pyrtl.reset_working_block()
    pyrtl.set_debug_mode(True)

    # setup
    basic_setup()

    # test
    sim_trace = pyrtl.SimulationTrace()
    sim = pyrtl.Simulation(tracer=sim_trace)

    for bitstring in itertools.product(range(2), repeat=8): # all length 8 bit strings
        inputs = {
            "start": 0,
            "var_vals_0": bitstring[0],
            "var_vals_1": bitstring[1],
            "var_vals_2": bitstring[2],
            "var_vals_3": bitstring[3],
            "var_assigned_0": bitstring[4],
            "var_assigned_1": bitstring[5],
            "var_assigned_2": bitstring[6],
            "var_assigned_3": bitstring[7]
        }
        sim.step(inputs)
        assert sim_trace.trace["test_active"][-1] == 0
        assert sim_trace.trace["status"][-1] == 0
        assert sim_trace.trace["va_write_enable"][-1] == 0
        # todo check that variables aren't changing but also we need to assign some values to the clause storage

# test that the bcp will run a second loop after assigning a variable
def bcp_write_loop_test():
    pyrtl.reset_working_block()
    pyrtl.set_debug_mode(True)

    # setup
    bcp = basic_setup()
    # x1 ~x2 x3 ~x4
    # 000000001
    # 100000010
    # 000000011
    # 100000100
    memory = {
        0xAA: 0b100000100000000011100000010000000001
    }

    # test
    sim_trace = pyrtl.SimulationTrace()
    sim = pyrtl.Simulation(tracer=sim_trace, memory_value_map={bcp.clause_storage.mem: memory})

    input = copy.deepcopy(DEFAULT_INPUT)
    input["start"] = 1
    sim.step(input)
    for i in range(170):
        sim.step(DEFAULT_INPUT)
        assert sim_trace.trace["va_addrs_0"][-1] == 0
        assert sim_trace.trace["test_active"][-1] == 1
        assert sim_trace.trace["va_write_enable"][-1] == 0

    input = copy.deepcopy(DEFAULT_INPUT)
    # x1 and x3 is false, x4 is true so that x2 is implied false
    input["var_vals_0"] = 0
    input["var_assigned_0"] = 1
    input["var_vals_1"] = 0
    input["var_assigned_1"] = 0
    input["var_vals_2"] = 0
    input["var_assigned_2"] = 1
    input["var_vals_3"] = 1
    input["var_assigned_3"] = 1
    sim.step(input)

    assert sim_trace.trace["va_addrs_0"][-1] == 1
    assert sim_trace.trace["va_addrs_1"][-1] == 2
    assert sim_trace.trace["va_addrs_2"][-1] == 3
    assert sim_trace.trace["va_addrs_3"][-1] == 4

    assert sim_trace.trace["test_active"][-1] == 1

    assert sim_trace.trace["va_write_enable"][-1] == 1
    assert sim_trace.trace["va_write_addr"][-1] == 2
    assert sim_trace.trace["va_write_val"][-1] == 0

    for i in range(85):
        sim.step(DEFAULT_INPUT)
        assert sim_trace.trace["test_active"][-1] == 1

    # second iteration

    for i in range(256):
        sim.step(DEFAULT_INPUT)
        assert sim_trace.trace["test_active"][-1] == 1
    sim.step(DEFAULT_INPUT)
    assert sim_trace.trace["test_active"][-1] == 0

def bcp_chain_implication_test():
    pyrtl.reset_working_block()
    pyrtl.set_debug_mode(True)

    # setup
    bcp = basic_setup()
    # x1
    # x2 ~x1
    # x3 ~x2 ~x1
    # x4 ~x3 ~x2 ~x1
    memory = {
        0x01: 0b000000000000000000000000000000000001,
        0x02: 0b000000000000000000100000001000000010,
        0x03: 0b000000000100000001100000010000000011,
        0x04: 0b100000001100000010100000011000000100
    }

    sim_trace = pyrtl.SimulationTrace()
    sim = pyrtl.Simulation(tracer=sim_trace, memory_value_map={bcp.clause_storage.mem: memory})

    input = copy.deepcopy(DEFAULT_INPUT)
    input["start"] = 1
    sim.step(input)
    sim.step(DEFAULT_INPUT)

    input = copy.deepcopy(DEFAULT_INPUT)
    input["var_vals_0"] = 0
    input["var_assigned_0"] = 0
    input["var_vals_1"] = 0
    input["var_assigned_1"] = 0
    input["var_vals_2"] = 0
    input["var_assigned_2"] = 0
    input["var_vals_3"] = 0
    input["var_assigned_3"] = 0
    sim.step(input)

    assert sim_trace.trace["va_addrs_0"][-1] == 1
    assert sim_trace.trace["va_addrs_1"][-1] == 0
    assert sim_trace.trace["va_addrs_2"][-1] == 0
    assert sim_trace.trace["va_addrs_3"][-1] == 0

    assert sim_trace.trace["test_active"][-1] == 1

    assert sim_trace.trace["va_write_enable"][-1] == 1
    assert sim_trace.trace["va_write_addr"][-1] == 1
    assert sim_trace.trace["va_write_val"][-1] == 1

    input = copy.deepcopy(DEFAULT_INPUT)
    input["var_vals_0"] = 0
    input["var_assigned_0"] = 0
    input["var_vals_1"] = 1
    input["var_assigned_1"] = 1
    input["var_vals_2"] = 0
    input["var_assigned_2"] = 0
    input["var_vals_3"] = 0
    input["var_assigned_3"] = 0
    sim.step(input)

    assert sim_trace.trace["va_addrs_0"][-1] == 2
    assert sim_trace.trace["va_addrs_1"][-1] == 1
    assert sim_trace.trace["va_addrs_2"][-1] == 0
    assert sim_trace.trace["va_addrs_3"][-1] == 0

    assert sim_trace.trace["test_active"][-1] == 1

    assert sim_trace.trace["va_write_enable"][-1] == 1
    assert sim_trace.trace["va_write_addr"][-1] == 2
    assert sim_trace.trace["va_write_val"][-1] == 1

    input = copy.deepcopy(DEFAULT_INPUT)
    input["var_vals_0"] = 0
    input["var_assigned_0"] = 0
    input["var_vals_1"] = 1
    input["var_assigned_1"] = 1
    input["var_vals_2"] = 1
    input["var_assigned_2"] = 1
    input["var_vals_3"] = 0
    input["var_assigned_3"] = 0
    sim.step(input)

    assert sim_trace.trace["va_addrs_0"][-1] == 3
    assert sim_trace.trace["va_addrs_1"][-1] == 2
    assert sim_trace.trace["va_addrs_2"][-1] == 1
    assert sim_trace.trace["va_addrs_3"][-1] == 0

    assert sim_trace.trace["test_active"][-1] == 1

    assert sim_trace.trace["va_write_enable"][-1] == 1
    assert sim_trace.trace["va_write_addr"][-1] == 3
    assert sim_trace.trace["va_write_val"][-1] == 1

    input = copy.deepcopy(DEFAULT_INPUT)
    input["var_vals_0"] = 0
    input["var_assigned_0"] = 0
    input["var_vals_1"] = 1
    input["var_assigned_1"] = 1
    input["var_vals_2"] = 1
    input["var_assigned_2"] = 1
    input["var_vals_3"] = 1
    input["var_assigned_3"] = 1
    sim.step(input)

    assert sim_trace.trace["va_addrs_0"][-1] == 4
    assert sim_trace.trace["va_addrs_1"][-1] == 3
    assert sim_trace.trace["va_addrs_2"][-1] == 2
    assert sim_trace.trace["va_addrs_3"][-1] == 1

    assert sim_trace.trace["test_active"][-1] == 1

    assert sim_trace.trace["va_write_enable"][-1] == 1
    assert sim_trace.trace["va_write_addr"][-1] == 4
    assert sim_trace.trace["va_write_val"][-1] == 1

tests = [
    bcp_inactive_test,
    bcp_write_loop_test,
    bcp_chain_implication_test
]

if __name__ == "__main__":
    for test in tests:
        print("Running", test.__name__)
        test()

# note this doesn't acutally work down here, you need to put it into a function before the asserts that are breaking
# sim_trace.render_trace()
