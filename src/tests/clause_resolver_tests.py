import pyrtl
from pyrtl import WireVector, Input, Output
import pathlib
import sys
import random
import copy

# slightly sketchy way to allow upward imports
directory = pathlib.Path(__file__)
sys.path.append(str(directory.parents[1]))

from bcp import ClauseResolver

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
    "cs_vars_0": 0,
    "cs_vars_1": 0,
    "cs_vars_2": 0,
    "cs_vars_3": 0,
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

# TODO: test the functional part of the clause resolver
#  * sat
#  * unsat
#  * unknown (2 vars)
#  * unknown (4 vars)
#  * implied true
#  * implied false

tests = [
    clause_resolver_addr_test
]

if __name__ == "__main__":
    for test in tests:
        print("Running", test.__name__)
        test()
