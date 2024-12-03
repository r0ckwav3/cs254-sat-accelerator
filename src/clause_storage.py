import pyrtl
from helpers import wirevector_list

# exposed wires:
#  * addr_i: read address input
#  * mem_o : raw output of the memory
#  * vars_o: array of wires carrying variable ids
#  * negs_o: array of bits indicating negation
class ClauseStorage:
    def __init__(self, clause_bits: int, var_bits:int, clause_size: int):
        self.addr_width = clause_bits
        self.var_bits = var_bits
        self.clause_size = clause_size

        store_width = (var_bits + 1) * clause_size
        self.mem = pyrtl.MemBlock(
            bitwidth = store_width,
            addrwidth = clause_bits,
            name = "Clause Storage",
            max_read_ports = 1,
            max_write_ports = 1
        )

        self.addr_i = pyrtl.WireVector(bitwidth = clause_bits, name="cs_addr_i")
        self.mem_o = pyrtl.WireVector(bitwidth = store_width, name="cs_mem_o")
        self.mem_o <<= self.mem[self.addr_i]

        self.vars_o = wirevector_list(var_bits, "cs_var_o", clause_size)
        self.negs_o = wirevector_list(1, "cs_neg_o", clause_size)
        for i in range(clause_size):
            var_start = i * (var_bits + 1)
            self.vars_o[i] <<= self.mem_o[var_start:var_start+var_bits]
            self.negs_o[i] <<= self.mem_o[var_start+var_bits:var_start+var_bits+1]

        # TODO: implement write i/o
