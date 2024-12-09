import pyrtl
import helpers
from pyrtl import WireVector, Register
from helpers import wirevector_list, connect_wire_lists, map_wires
from clause_resolver import ClauseResolver
from clause_storage import ClauseStorage
from bcp import BCP
from var_assign_store import VarAssignStore
import io

##################### Random stuff #####################
def get_val_bit(a):
    ans = WireVector(bitwidth=1)
    ans <<= a[1]
    return ans

def get_assigned_bit(a):
    ans = WireVector(bitwidth=1)
    ans <<= a[0]
    return ans

##################### Constants #####################

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
prev_state = pyrtl.Register(bitwidth=2, name="prev_state")
new_dpll_state = pyrtl.WireVector(bitwidth=2, name="new_dpll_state")
curr_level = pyrtl.Register(bitwidth=VAR_BITS+1, name="curr_level")
next_level = pyrtl.WireVector(bitwidth=VAR_BITS+1, name="next_level")

sat_state = pyrtl.Register(bitwidth=1, name="sat_state")
next_sat_state = pyrtl.WireVector(bitwidth=1, name="next_sat_state")

backtrack_write_val = pyrtl.WireVector(bitwidth = 4 + 2*VAR_BITS, name="backtrack_write_val")
backtrack_write_enable = pyrtl.WireVector(bitwidth=1, name="backtrack_write_enable")

var_assign_store = VarAssignStore(CLAUSE_BITS, VAR_BITS, CLAUSE_SIZE)

# hi jon i didn't want to write this
every_assigned_bit = map_wires(var_assign_store.every_memory_value, get_assigned_bit)
every_assigned_bit_with_names = wirevector_list(1, "every_assigned_bit_with_names", 2 ** VAR_BITS)
connect_wire_lists(every_assigned_bit_with_names, every_assigned_bit)

every_val_bit = map_wires(var_assign_store.every_memory_value, get_val_bit)
every_val_bit_with_names = wirevector_list(1, "every_val_bit_with_names", 2 ** VAR_BITS)
connect_wire_lists(every_val_bit_with_names, every_val_bit)

# set up BCP to default values
bcp = BCP(CLAUSE_BITS, VAR_BITS, CLAUSE_SIZE)
# connect the bcp up to var assign store
raw_bcp_varassigns = wirevector_list(4 + VAR_BITS * 2, "raw_bcp_varassigns", CLAUSE_SIZE)
bcp_to_write = WireVector(4 + VAR_BITS * 2, "bcp_to_write")
connect_wire_lists(
    raw_bcp_varassigns,
    map_wires(bcp.va_addrs_o, lambda x: var_assign_store.mem[x])
)
connect_wire_lists(
    bcp.var_vals_i,
    map_wires(raw_bcp_varassigns, lambda x: x[1])
)
connect_wire_lists(
    bcp.var_assigned_i,
    map_wires(raw_bcp_varassigns, lambda x: x[0])
)
bcp_to_write <<= pyrtl.concat(bcp.va_write_addr_o, curr_level, bcp.va_write_val_o, pyrtl.Const(1, bitwidth=1))
var_assign_store.mem[bcp.va_write_addr_o] <<= pyrtl.MemBlock.EnabledWrite(
    bcp_to_write, enable=bcp.va_write_enable_o
)

with pyrtl.conditional_assignment:
    with dpll_state == 0:
        # assign/start
        var_assign_store.start |= 1
        var_assign_store.level |= 0

        #see what we get
        with var_assign_store.sat:
            new_dpll_state |= 3
            next_sat_state |= 1
            sat |= 1
            done |= 1
        with var_assign_store.ready_bcp:
            new_dpll_state |= 1
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
        with ~bcp.active_o & (prev_state != 1):
            # first cycle, start it up
            bcp.start_i |= 1
            new_dpll_state |= 1
            next_level |= curr_level
        with bcp.active_o:
            # still running
            new_dpll_state |= 1
            next_level |= curr_level
        with ~bcp.active_o & (prev_state == 1):
            # finished
            with bcp.status_o:
                # failed
                new_dpll_state |= 2
                next_level |= curr_level
            with pyrtl.otherwise:
                # suceeded
                new_dpll_state |= 0
                next_level |= curr_level + 1

        next_sat_state |= 0
        sat |= 0
        done |= 0
    with dpll_state == 2:
        # backtrack
        with var_assign_store.has_current_level:
            backtrack_write_enable |= 1
            next_level |= curr_level
            with ~var_assign_store.currlevel_check[3+VAR_BITS * 2]:
                # it's not the root
                backtrack_write_val |= pyrtl.concat(var_assign_store.current_level_addr, pyrtl.Const(0, bitwidth=3+VAR_BITS))
                new_dpll_state |= 2
            with pyrtl.otherwise:
                # it's the root
                with ~var_assign_store.currlevel_check[1]:
                    # it was a 0, set it to 1 and bcp again
                    backtrack_write_val |= pyrtl.concat(pyrtl.Const(1, bitwidth=1), var_assign_store.current_level_addr, curr_level, pyrtl.Const(0b11, bitwidth=2))
                    new_dpll_state |= 1
                with pyrtl.otherwise:
                    # it was a 1, set it to bad state and go to assign
                    backtrack_write_val |= pyrtl.concat(pyrtl.Const(1, bitwidth=1), var_assign_store.current_level_addr, curr_level, pyrtl.Const(0b10, bitwidth=2))
                    new_dpll_state |= 0

        with pyrtl.otherwise:
            new_dpll_state |= 0
            next_level |= curr_level - 1
        next_sat_state |= 0
        sat |= 0
        done |= 0
    with dpll_state == 3:
        # done, stay in this state
        new_dpll_state |= 3
        next_sat_state |= sat_state
        sat |= sat_state
        done |= 1

var_assign_store.mem[var_assign_store.current_level_addr] <<= pyrtl.MemBlock.EnabledWrite(
    backtrack_write_val,
    backtrack_write_enable
)

dpll_state.next <<= new_dpll_state
prev_state.next <<= dpll_state
curr_level.next <<= next_level
sat_state.next <<= next_sat_state


##################### SIMULATION #####################

if __name__ == '__main__':
    memory = {
        0x01: 0b000000000000000000000000000000000001,
        0x02: 0b000000000000000000100000001000000010,
        0x03: 0b000000000100000001100000010000000011,
        0x04: 0b100000001100000010100000011000000100,
        0x05: 0b000000000000000000000000000100000100
    }

    var_mem = {0x00: 0b00000000000000000}
    for i in range(256):
        val = (i << 11)
        var_mem[i] = val

    # for i in range(256):
    #     print("{:019b}".format(var_mem[i]))

    sim_trace = pyrtl.SimulationTrace()
    sim = pyrtl.Simulation(tracer=sim_trace, memory_value_map={var_assign_store.mem: var_mem, bcp.clause_storage.mem: memory})
    #sim = pyrtl.Simulation(tracer=sim_trace, memory_value_map={bcp.clause_storage.mem: memory})

    for cycle in range(18):
        sim.step({})

    sim_trace.render_trace(symbol_len = 7)

    print('mem',sim.inspect_mem(var_assign_store.mem))

    # with io.StringIO() as vfile:
    #     pyrtl.output_to_graphviz(vfile)
    #     f = open("dpll_graph.gv", "a")
    #     f.write(vfile.getvalue())
    #     f.close()
