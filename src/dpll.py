import pyrtl
import helpers
from pyrtl import WireVector, Register
from helpers import wirevector_list, connect_wire_lists
from clause_resolver import ClauseResolver
from clause_storage import ClauseStorage
from bcp import BCP
from var_assign_store import VarAssignStore


CLAUSE_BITS = 8 # we have <= 2^CLAUSE_BITS clauses
VAR_BITS    = 8 # we have <= 2^VAR_BITS clauses
CLAUSE_SIZE = 4 # each clause has <= CLAUSE_SIZE vars in it

##################### DPLL starts here #####################
sat = pyrtl.Output(bitwidth=1, name='sat')
done = pyrtl.Output(bitwidth=1, name='done')

# STATES
# 00: Assign/Start
# 01: BCP
# 10: Backtrack
# 11: Done
dpll_state = pyrtl.Register(bitwidth=2, name="dpll_state")
new_dpll_state = pyrtl.WireVector(bitwidth=2, name="new_dpll_state")
curr_level = pyrtl.Register(bitwidth=VAR_BITS, name="curr_level")
next_level = pyrtl.WireVector(bitwidth=2, name="next_level")

sat_state = pyrtl.Register(bitwidth=1, name="sat_state")
next_sat_state = pyrtl.WireVector(bitwidth=1, name="next_sat_state")

var_assign_store = VarAssignStore(8, 8, 4)

# set up BCP to default values
#bcp = BCP(CLAUSE_BITS, VAR_BITS, CLAUSE_SIZE)

#bcp.start_i <<= 0
#connect_wire_lists(bcp.var_vals_i, wirevector_list(1, "var_vals", CLAUSE_SIZE))

with pyrtl.conditional_assignment:
    with dpll_state == 0:
        # assign/start
        var_assign_store.start <<= 1
        var_assign_store.level <<= 0

        #see what we get
        with var_assign_store.sat:
            new_dpll_state |= 3
            next_sat_state |= 1
            sat |= 1
            done |= 1
        with var_assign_store.ready_bcp:
            new_dpll_state |= 0
            next_sat_state |= 0
            sat |= 0
            done |= 0
            next_level |= curr_level
        with var_assign_store.needs_backtrack:
            new_dpll_state |= 2
            next_sat_state |= 0
            sat |= 0
            done |= 0
            next_level |= curr_level
        with var_assign_store.unsat:
            new_dpll_state |= 3
            next_sat_state |= 0
            sat |= 0
            done |= 1 

    with dpll_state == 1:
        # BCP
        new_dpll_state |= 0
        next_sat_state |= 0
        sat |= 0
        done |= 0
        next_level |= curr_level
    with dpll_state == 2:
        # backtrack
        new_dpll_state |= 0
        next_sat_state |= 0
        sat |= 0
        done |= 0
        next_level |= curr_level
    with dpll_state == 3:
        # done, stay in this state
        new_dpll_state |= 3
        next_sat_state |= sat_state
        sat |= sat_state
        done |= 1

dpll_state.next <<= new_dpll_state
curr_level.next <<= next_level
sat_state.next <<= next_sat_state

##################### SIMULATION #####################

if __name__ == '__main__':
    memory = {
        0x01: 0b000000000000000000000000000000000001,
        0x02: 0b000000000000000000100000001000000010,
        0x03: 0b000000000100000001100000010000000011,
        0x04: 0b100000001100000010100000011000000100
    }

    var_mem = {0x00: 0b00000000000000000}
    for i in range(256):
        val = (i << 11)
        var_mem[i] = val
    
    # for i in range(256):
    #     print("{:019b}".format(var_mem[i]))

    sim_trace = pyrtl.SimulationTrace()
    sim = pyrtl.Simulation(tracer=sim_trace, memory_value_map={var_assign_store.mem: var_mem})
    #sim = pyrtl.Simulation(tracer=sim_trace, memory_value_map={bcp.clause_storage.mem: memory})

    for cycle in range(18):
        sim.step({})

    sim_trace.render_trace(symbol_len = 7) 
    
    print('mem',sim.inspect_mem(var_assign_store.mem))
