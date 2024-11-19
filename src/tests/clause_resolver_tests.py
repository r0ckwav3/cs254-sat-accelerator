import pyrtl
from pyrtl import WireVector, Input, Output
import pathlib
import sys
import random
import copy

# slightly sketchy way to allow upward imports
directory = pathlib.Path(__file__)
sys.path.append(str(directory.parents[1]))

from clause_resolver import ClauseResolver
import helpers

def basic_setup():
    clause_resolver = ClauseResolver(8, 8, 4)
    clause_resolver.clause_id_i <<= Input(bitwidth = 8, name = "clause_id")
    clause_resolver.cs_vars_i[0] <<= Input(bitwidth = 8, name = "cs_vars_0")
    clause_resolver.cs_vars_i[1] <<= Input(bitwidth = 8, name = "cs_vars_1")
    clause_resolver.cs_vars_i[2] <<= Input(bitwidth = 8, name = "cs_vars_2")
    clause_resolver.cs_vars_i[3] <<= Input(bitwidth = 8, name = "cs_vars_3")
    clause_resolver.cs_negated_i[0] <<= Input(bitwidth = 1, name = "cs_negated_0")
    clause_resolver.cs_negated_i[1] <<= Input(bitwidth = 1, name = "cs_negated_1")
    clause_resolver.cs_negated_i[2] <<= Input(bitwidth = 1, name = "cs_negated_2")
    clause_resolver.cs_negated_i[3] <<= Input(bitwidth = 1, name = "cs_negated_3")
    clause_resolver.var_vals_i[0] <<= Input(bitwidth = 1, name = "var_vals_0")
    clause_resolver.var_vals_i[1] <<= Input(bitwidth = 1, name = "var_vals_1")
    clause_resolver.var_vals_i[2] <<= Input(bitwidth = 1, name = "var_vals_2")
    clause_resolver.var_vals_i[3] <<= Input(bitwidth = 1, name = "var_vals_3")
    clause_resolver.var_assigned_i[0] <<= Input(bitwidth = 1, name = "var_assigned_0")
    clause_resolver.var_assigned_i[1] <<= Input(bitwidth = 1, name = "var_assigned_1")
    clause_resolver.var_assigned_i[2] <<= Input(bitwidth = 1, name = "var_assigned_2")
    clause_resolver.var_assigned_i[3] <<= Input(bitwidth = 1, name = "var_assigned_3")

    cs_addr = Output(bitwidth = 8, name = "cs_addr")
    va_addrs_0 = Output(bitwidth = 8, name = "va_addrs_0")
    va_addrs_1 = Output(bitwidth = 8, name = "va_addrs_1")
    va_addrs_2 = Output(bitwidth = 8, name = "va_addrs_2")
    va_addrs_3 = Output(bitwidth = 8, name = "va_addrs_3")
    clause_status = Output(bitwidth = 2, name = "clause_status")
    implied_var = Output(bitwidth = 8, name = "implied_var")
    implied_val = Output(bitwidth = 1, name = "implied_val")

    cs_addr <<= clause_resolver.cs_addr_o
    va_addrs_0 <<= clause_resolver.va_addrs_o[0]
    va_addrs_1 <<= clause_resolver.va_addrs_o[1]
    va_addrs_2 <<= clause_resolver.va_addrs_o[2]
    va_addrs_3 <<= clause_resolver.va_addrs_o[3]
    clause_status <<= clause_resolver.clause_status_o
    implied_var <<= clause_resolver.implied_var_o
    implied_val <<= clause_resolver.implied_val_o

DEFAULT_INPUT = {
    "clause_id": 0,
    "cs_vars_0": 0x10,
    "cs_vars_1": 0x11,
    "cs_vars_2": 0x12,
    "cs_vars_3": 0x13,
    "cs_negated_0": 0,
    "cs_negated_1": 0,
    "cs_negated_2": 0,
    "cs_negated_3": 0,
    "var_vals_0": 0,
    "var_vals_1": 0,
    "var_vals_2": 0,
    "var_vals_3": 0,
    "var_assigned_0": 0,
    "var_assigned_1": 0,
    "var_assigned_2": 0,
    "var_assigned_3": 0
}

def clause_resolver_addr_test():
    pyrtl.reset_working_block()
    pyrtl.set_debug_mode(True)

    # setup
    basic_setup()

    # test
    sim_trace = pyrtl.SimulationTrace()
    sim = pyrtl.Simulation(tracer=sim_trace)

    inputs = copy.deepcopy(DEFAULT_INPUT)
    inputs["clause_id"] = 0x67
    inputs["cs_vars_0"] = 0x89
    inputs["cs_vars_1"] = 0xab
    inputs["cs_vars_2"] = 0xcd
    inputs["cs_vars_3"] = 0xef
    sim.step(inputs)

    assert sim_trace.trace["cs_addr"][-1] == 0x67
    assert sim_trace.trace["va_addrs_0"][-1] == 0x89
    assert sim_trace.trace["va_addrs_1"][-1] == 0xab
    assert sim_trace.trace["va_addrs_2"][-1] == 0xcd
    assert sim_trace.trace["va_addrs_3"][-1] == 0xef

def clause_resolver_sat_unsat_test():
    pyrtl.reset_working_block()
    pyrtl.set_debug_mode(True)

    # setup
    basic_setup()

    # test
    sim_trace = pyrtl.SimulationTrace()
    sim = pyrtl.Simulation(tracer=sim_trace)
    inputs = copy.deepcopy(DEFAULT_INPUT)

    inputs["var_assigned_0"] = 1
    inputs["var_assigned_1"] = 1
    inputs["var_assigned_2"] = 1
    inputs["var_assigned_3"] = 1

    # non-negated sat
    inputs["var_vals_0"] = 1
    sim.step(inputs)
    assert sim_trace.trace["clause_status"][-1] == 2

    # negated sat
    inputs["var_vals_0"] = 0
    inputs["cs_negated_0"] = 1
    inputs["cs_negated_1"] = 1
    inputs["cs_negated_2"] = 1
    inputs["cs_negated_3"] = 1
    sim.step(inputs)
    assert sim_trace.trace["clause_status"][-1] == 2

    # negated unsat
    inputs["var_vals_0"] = 1
    inputs["var_vals_1"] = 1
    inputs["var_vals_2"] = 1
    inputs["var_vals_3"] = 1
    sim.step(inputs)
    assert sim_trace.trace["clause_status"][-1] == 1

    # mixed unsat
    inputs["var_vals_0"] = 0
    inputs["cs_negated_0"] = 0
    inputs["var_vals_2"] = 0
    inputs["cs_negated_2"] = 0
    sim.step(inputs)
    assert sim_trace.trace["clause_status"][-1] == 1

    # non-negated unsat
    inputs["var_vals_1"] = 0
    inputs["cs_negated_1"] = 0
    inputs["var_vals_3"] = 0
    inputs["cs_negated_3"] = 0
    sim.step(inputs)
    assert sim_trace.trace["clause_status"][-1] == 1

def clause_resolver_unknown_test():
    pyrtl.reset_working_block()
    pyrtl.set_debug_mode(True)

    # setup
    basic_setup()

    # test
    sim_trace = pyrtl.SimulationTrace()
    sim = pyrtl.Simulation(tracer=sim_trace)
    inputs = copy.deepcopy(DEFAULT_INPUT)

    # all unassigned test
    inputs["var_vals_0"] = 1
    inputs["cs_negated_1"] = 1
    inputs["cs_negated_3"] = 1
    sim.step(inputs)
    assert sim_trace.trace["clause_status"][-1] == 0

    # two unassigned test
    inputs["var_assigned_2"] = 1
    inputs["var_assigned_3"] = 1
    inputs["var_vals_3"] = 1
    sim.step(inputs)
    assert sim_trace.trace["clause_status"][-1] == 0

def clause_resolver_implied_test():
    pyrtl.reset_working_block()
    pyrtl.set_debug_mode(True)

    # setup
    basic_setup()

    # test
    sim_trace = pyrtl.SimulationTrace()
    sim = pyrtl.Simulation(tracer=sim_trace)
    inputs = copy.deepcopy(DEFAULT_INPUT)

    # var 2 implied true
    inputs["var_assigned_0"] = 1
    inputs["var_assigned_1"] = 1
    inputs["var_assigned_2"] = 0
    inputs["var_assigned_3"] = 1
    inputs["var_vals_0"] = 1
    inputs["var_vals_1"] = 0
    inputs["var_vals_2"] = 0
    inputs["var_vals_3"] = 1
    inputs["cs_negated_0"] = 1
    inputs["cs_negated_1"] = 0
    inputs["cs_negated_2"] = 0
    inputs["cs_negated_3"] = 1
    sim.step(inputs)
    assert sim_trace.trace["clause_status"][-1] == 3
    assert sim_trace.trace["implied_var"][-1] == 0x12
    assert sim_trace.trace["implied_val"][-1] == 1

    # var 1 implied false
    inputs["var_assigned_0"] = 1
    inputs["var_assigned_1"] = 0
    inputs["var_assigned_2"] = 1
    inputs["var_assigned_3"] = 1
    inputs["var_vals_0"] = 1
    inputs["var_vals_1"] = 0
    inputs["var_vals_2"] = 0
    inputs["var_vals_3"] = 1
    inputs["cs_negated_0"] = 1
    inputs["cs_negated_1"] = 1
    inputs["cs_negated_2"] = 0
    inputs["cs_negated_3"] = 1
    sim.step(inputs)
    assert sim_trace.trace["clause_status"][-1] == 3
    assert sim_trace.trace["implied_var"][-1] == 0x11
    assert sim_trace.trace["implied_val"][-1] == 0

tests = [
    clause_resolver_addr_test,
    clause_resolver_sat_unsat_test,
    clause_resolver_unknown_test,
    clause_resolver_implied_test
]

if __name__ == "__main__":
    for test in tests:
        print("Running", test.__name__)
        test()

# note this doesn't acutally work down here, you need to put it into a dunction before the asserts that are breaking
# sim_trace.render_trace()
