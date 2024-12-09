import pyrtl
import dpll
from consts import CLAUSE_BITS, VAR_BITS, CLAUSE_SIZE

MAX_ITERS = 1000

instance_path = "instances/example/sat-1.cnf"

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

# setup memories
var_mem = {0x00: 0b00000000000000000}
for i in range(256):
    val = (i << 11)
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
