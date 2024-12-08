from consts import CLAUSE_BITS, VAR_BITS, CLAUSE_SIZE

instance_path = "instances/example/sat-1"

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
                else:
                    memval = (memval<<(VAR_BITS+1)) + int(var[1:])
            memory[clause_counter] = memval
            clause_counter+=1
