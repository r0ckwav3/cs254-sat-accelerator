import pyrtl
from pyrtl import Input, Output
import pathlib
import sys
import copy
import itertools

# slightly sketchy way to allow upward imports
directory = pathlib.Path(__file__)
sys.path.append(str(directory.parents[1]))

from var_assign_store import VarAssignStore
from helpers import connect_wire_lists, wirevector_list

def basic_setup():
    vas = VarAssignStore(8, 8, 4)
    vas.start <<= Input(bitwidth = 1, name = "start")
    vas.level <<= Input(bitwidth = 1, name = "level")

    #active = Output(bitwidth = 1, name = "test_active")
    needs_backtrack = Output(bitwidth = 1, name = "needs_backtrack")
    unsat = Output(bitwidth = 1, name = "unsat")
    sat = Output(bitwidth = 1, name = "sat")
    ready_bcp = Output(bitwidth = 1, name = "ready_bcp")

    #active <<= vas.active
    needs_backtrack <<= vas.needs_backtrack
    unsat <<= vas.unsat
    sat <<= vas.sat
    ready_bcp <<= vas.ready_bcp

    return vas

DEFAULT_INPUT = {
    "start": 0,
    "level": 0,
}

def inactive_test():
    pyrtl.reset_working_block()
    pyrtl.set_debug_mode(True)

    # setup
    basic_setup()

    # test
    sim_trace = pyrtl.SimulationTrace()
    sim = pyrtl.Simulation(tracer=sim_trace)

    inputs = {
        "start": 0,
        "level": 1
    }
    sim.step(inputs)

    assert sim_trace.trace["assign_needs_backtrack"][-1] == 0
    assert sim_trace.trace["assign_ready_bcp"][-1] == 0
    assert sim_trace.trace["assign_sat"][-1] == 0
    assert sim_trace.trace["assign_unsat"][-1] == 0
    assert sim_trace.trace["assign_level"][-1] == 1

    #sim_trace.render_trace(symbol_len=40)

def sat_test():
    pyrtl.reset_working_block()
    pyrtl.set_debug_mode(True)

    # setup
    vas = basic_setup()

    # bits: 0 assigned, 1 val, 2 - 10 level, 11 - 19 address
    memory = {
        0x00: 0b00000000000000011,
        0x01: 0b00000100000000011,
        0x02: 0b00001000000000011,
        0x03: 0b00001100000000011,
        0x04: 0b00010000000000011,
        #0x05: 0b11111100000000011,
    } # all assigned to 1, no bt needed

    for i in range(64):
        val = (i << 12) | 0b00000000000000011
        memory[i] = val
    
    # for i in range(64):
    #     print(f"{memory[i]:b}")

    # test
    sim_trace = pyrtl.SimulationTrace()
    sim = pyrtl.Simulation(tracer=sim_trace, memory_value_map={
        vas.mem : memory
    })

    inputs = {
        "start": 1,
        "level": 1
    }
    sim.step(inputs)

    
    assert sim_trace.trace["assign_needs_backtrack"][-1] == 0
    assert sim_trace.trace["assign_ready_bcp"][-1] == 0
    assert sim_trace.trace["assign_sat"][-1] == 1
    assert sim_trace.trace["assign_unsat"][-1] == 0
    assert sim_trace.trace["assign_level"][-1] == 1
    
    #sim_trace.render_trace(symbol_len=100)
    
def needs_backtrack_test():
    pyrtl.reset_working_block()
    pyrtl.set_debug_mode(True)

    # setup
    vas = basic_setup()

     # bits: 0 assigned, 1 val, 2 - 10 level, 11 - 19 address
    memory = {
        0x00: 0b00000000000000011,
        0x01: 0b00000100000000011,
        0x02: 0b00001000000000011,
        0x03: 0b00001100000000011,
        0x04: 0b00010000000001101,
    } # all assigned to 1 except for x4, which needs backtracking

    # test
    sim_trace = pyrtl.SimulationTrace()
    sim = pyrtl.Simulation(tracer=sim_trace, memory_value_map={
        vas.mem : memory
    })

    inputs = {
        "start": 1,
        "level": 1
    }
    sim.step(inputs)

    
    assert sim_trace.trace["assign_needs_backtrack"][-1] == 1
    assert sim_trace.trace["assign_ready_bcp"][-1] == 0
    assert sim_trace.trace["assign_sat"][-1] == 0
    assert sim_trace.trace["assign_unsat"][-1] == 0
    assert sim_trace.trace["assign_level"][-1] == 1
    
    # sim_trace.render_trace(symbol_len=100)

def unsat_test():
    pyrtl.reset_working_block()
    pyrtl.set_debug_mode(True)

    # setup
    vas = basic_setup()

     # bits: 0 assigned, 1 val, 2 - 10 level, 11 - 19 address
    memory = {
        0x00: 0b00000000000000011,
        0x01: 0b00000100000000011,
        0x02: 0b00001000000000011,
        0x03: 0b00001100000000011,
        0x04: 0b00010000000000001,
    } # all assigned to 1 except for x4, which needs backtracking

    # test
    sim_trace = pyrtl.SimulationTrace()
    sim = pyrtl.Simulation(tracer=sim_trace, memory_value_map={
        vas.mem : memory
    })

    inputs = {
        "start": 1,
        "level": 0
    }
    sim.step(inputs)

    
    assert sim_trace.trace["assign_needs_backtrack"][-1] == 0
    assert sim_trace.trace["assign_ready_bcp"][-1] == 0
    assert sim_trace.trace["assign_sat"][-1] == 0
    assert sim_trace.trace["assign_unsat"][-1] == 1
    assert sim_trace.trace["assign_level"][-1] == 0
    
    #sim_trace.render_trace(symbol_len=100)

def assign_test():
    pyrtl.reset_working_block()
    pyrtl.set_debug_mode(True)

    # setup
    vas = basic_setup()

     # bits: 0 assigned, 1 val, 2 - 10 level, 11 - 18 address
    memory = {
        0x00: 0b00000000000000011,
        0x01: 0b00000100000000011,
        0x02: 0b00001000000000011,
        0x03: 0b00001100000000011,
        0x04: 0b00010000000000000,
    } # all assigned to 1 except for x4, which needs backtracking

    # test
    sim_trace = pyrtl.SimulationTrace()
    sim = pyrtl.Simulation(tracer=sim_trace, memory_value_map={
        vas.mem : memory
    })

    inputs = {
        "start": 1,
        "level": 1 #BUG: can't make this greater than 1 for some reason????
    }
    sim.step(inputs)

    
    assert sim_trace.trace["assign_needs_backtrack"][-1] == 0
    assert sim_trace.trace["assign_ready_bcp"][-1] == 1
    assert sim_trace.trace["assign_sat"][-1] == 0
    assert sim_trace.trace["assign_unsat"][-1] == 0
    assert sim_trace.trace["assign_level"][-1] == 1

    #print((sim_trace.trace["assign_new_assign"][0]))
    assert sim_trace.trace["assign_new_assign"][-1] == 0b00010000000000101

    #print(sim.inspect_mem(vas.mem))
    assert sim.inspect_mem(vas.mem)[0x04] == 0b00010000000000101
    
    #sim_trace.render_trace(symbol_len=100)

tests = [
    needs_backtrack_test,
    inactive_test,
    sat_test,
    unsat_test,
    assign_test,
]

if __name__ == "__main__":
    for test in tests:
        print("Running", test.__name__)
        test()