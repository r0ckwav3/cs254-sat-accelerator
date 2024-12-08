import pyrtl
import helpers
from pyrtl import WireVector, Register
from helpers import wirevector_list, connect_wire_lists
from clause_resolver import ClauseResolver
from clause_storage import ClauseStorage
from bcp import BCP


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
new_dpll_state = pyrtl.WireVector(bitwidth=2, name="new_pred_state")

var_mem = pyrtl.MemBlock(
    bitwidth = 3 + VAR_BITS, # 1 for assigned, 1 for val, VAR_BITS + 1 for level
    addrwidth = VAR_BITS,
    name = "Variable Memory",
    max_read_ports = 1,
    max_write_ports = 1
)

# set up BCP to default values
bcp = BCP(CLAUSE_BITS, VAR_BITS, CLAUSE_SIZE)

bcp.start_i <<= 0
connect_wire_lists(bcp.var_vals_i, wirevector_list(1, "var_vals", CLAUSE_SIZE))

with pyrtl.conditional_assignment:
    with dpll_state == 0:
        # check if we have any unassigned variables

        new_dpll_state |= 1
        sat |= 0
        done |= 0
    with dpll_state == 1:
        # BCP

        new_dpll_state |= 2
        sat |= 0
        done |= 0
    with dpll_state == 2:
        # backtrack

        new_dpll_state |= 3
        sat |= 0
        done |= 0
    with dpll_state == 3:
        # done, stay in this state
        new_dpll_state |= 3
        sat |= 1
        done |= 1

dpll_state.next <<= new_dpll_state

##################### SIMULATION #####################

if __name__ == '__main__':
    memory = {
        0x01: 0b000000000000000000000000000000000001,
        0x02: 0b000000000000000000100000001000000010,
        0x03: 0b000000000100000001100000010000000011,
        0x04: 0b100000001100000010100000011000000100
    }

    sim_trace = pyrtl.SimulationTrace()
    sim = pyrtl.Simulation(tracer=sim_trace, memory_value_map={bcp.clause_storage.mem: memory})

    for cycle in range(10):
        sim.step({})

    sim_trace.render_trace(symbol_len = 5) 
    
    print('mem',sim.inspect_mem(bcp.clause_storage.mem))
