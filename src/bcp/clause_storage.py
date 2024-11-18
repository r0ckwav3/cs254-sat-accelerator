import pyrtl

# exposed wires:
#  * addr_i: read address input
#  * mem_o : raw output of the memory
#  * vars_o: array of wires carrying variable ids
#  * negs_o: array of bits indicating negation
class ClauseStorage:
    def __init__(self, addr_width: int, var_bits:int, clause_size: int):
        self.addr_width = addr_width
        self.var_bits = var_bits
        self.clause_size = clause_size

        store_width = (var_bits + 1) * clause_size
        self.mem = pyrtl.MemBlock(
            bitwidth = store_width,
            addrwidth = addr_width,
            name = "Clause Storage",
            max_read_ports = 1,
            max_write_ports = 1
        )

        self.addr_i = pyrtl.WireVector(bitwidth = addr_width, name="cs_addr_i")
        self.mem_o = pyrtl.WireVector(bitwidth = store_width, name="cs_mem_o")
        self.mem_o <<= self.mem[self.addr_i]

        self.vars_o = []
        self.negs_o = []
        for i in range(clause_size):
            temp_var = pyrtl.WireVector(bitwidth = var_bits, name=f"cs_var_o_{i}")
            temp_neg = pyrtl.WireVector(bitwidth = 1, name=f"cs_neg_o_{i}")
            var_start = i * (var_bits + 1)
            temp_var <<= self.mem_o[var_start:var_start+var_bits]
            temp_neg <<= self.mem_o[var_start+var_bits:var_start+var_bits+1]
            self.vars_o.append(temp_var)
            self.vars_o.append(temp_neg)

        # TODO: implement write i/o
