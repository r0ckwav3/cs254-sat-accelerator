import pyrtl
import dpll
from consts import CLAUSE_BITS, VAR_BITS, CLAUSE_SIZE

MAX_ITERS = 1000

instance_path = "instances/example/unsat-1.cnf"
# instance_path = "instances/uuf50-218/uuf50-01.cnf"

# parse instance
memory = {}
clause_counter = 0

with open(instance_path, "r") as instance:
    for line in instance.readlines():
        if len(line) == 0:
            continue
        elif line[0] == "c" or line[0] == "%":
            continue
        elif line[0] == "p":
            words = line.split()
            print(f"header: {line}")
            assert words[1] == "cnf"
            assert int(words[2]) < (1<<VAR_BITS)
            assert int(words[3]) < (1<<CLAUSE_BITS)
        else:
            vars = line.split()
            assert len(vars)-1 <= CLAUSE_SIZE
            memval = 0
            for var in vars:
                if var[0] == "-":
                    memval = (memval<<(VAR_BITS+1)) + (1<<(VAR_BITS)) + int(var[1:])
                elif var != "0":
                    memval = (memval<<(VAR_BITS+1)) + int(var)

            if memval == 0:
                # a bunch of the test cases are just a singular 0
                continue
            memory[clause_counter] = memval
            clause_counter+=1

# setup
var_mem = {}
for i in range(1<<VAR_BITS):
    val = (i << (3+VAR_BITS))
    var_mem[i] = val

sim_trace = pyrtl.SimulationTrace()
sim = pyrtl.Simulation(tracer=sim_trace, memory_value_map={dpll.var_assign_store.mem: var_mem, dpll.bcp.clause_storage.mem: memory})

# run
counter = 1
sim.step()
while counter < MAX_ITERS and sim_trace.trace["done"][-1] != 1:
    sim.step()
    counter += 1

finished = sim_trace.trace["done"][-1] == 1
is_sat = sim_trace.trace["sat"][-1] == 1
print(f"file: {instance_path}")
print(f"finished:{finished} sat:{is_sat} cycles:{counter}")

"""
sim_trace.render_trace(
    trace_list = ["done", "sat", "curr_level", "dpll_state", "clause_addr", "clause_status_o", "is_sat", "contradiction", "update_made", "unassigned_count", "bcp_va_write_addr_o", "bcp_va_write_enable_o", "bcp_status_o",
        "cs_negated_i_0", "cs_negated_i_1", "cs_negated_i_2", "cs_negated_i_3",
        "cs_vars_i_0", "cs_vars_i_1", "cs_vars_i_2", "cs_vars_i_3",
        "unassigned_0", "unassigned_1", "unassigned_2", "unassigned_3",
        "every_memory_value_1","every_memory_value_2","every_memory_value_3","every_memory_value_4","every_memory_value_5","every_memory_value_6","every_memory_value_7"],
    symbol_len=6
)
"""
