import pyrtl
from pyrtl import WireVector

# exposed wires:
# Inputs:
#  - clause_id_i:  id of clause to resolve
#  - cs_vars_i:    array of variables ids in this clause (from storage)
#  - cs_negated_i: array of variable negation bits for this clause
#  - var_vals_i:     values of variables (from storage)
#  - var_assigned_i: assigned bits of variables
# Outputs:
#  - cs_addr_o:       address sent to clause storage
#  - va_addrs_o:      addresses sent to variable assignment storage
#  - clause_status_o: returned status of the clause - 0:unknown, 1:unsat, 2: sat or 3: forced variable
#  - implied_var_o:   implied variable (if status = 3)
#  - implied_val_o:   implied value (if status = 3)

class ClauseResolver:
    def __init__(self, clause_bits: int, var_bits:int, clause_size: int):
        # IN
        self.clause_id_i = WireVector(bitwidth = clause_bits, name = "clause_id_i")
        self.cs_vars_i = [
            WireVector(bitwidth = var_bits, name = f"cs_vars_{i}_i")
            for i in range(clause_size)
        ]
        self.cs_negated_i = [
            WireVector(bitwidth = 1, name = f"cs_negated_{i}_i")
            for i in range(clause_size)
        ]
        self.var_vals_i = [
            WireVector(bitwidth = 1, name = f"var_vals_{i}_i")
            for i in range(clause_size)
        ]
        self.var_assigned_i = [
            WireVector(bitwidth = 1, name = f"var_assigned_{i}_i")
            for i in range(clause_size)
        ]

        # OUT
        self.cs_addr_o = WireVector(bitwidth = clause_bits, name = "cs_addr_o")
        self.va_addrs_o = [
            WireVector(bitwidth = var_bits, name = f"va_addrs_{i}_o")
            for i in range(clause_size)
        ]
        self.clause_status_o = WireVector(bitwidth = 2, name = "clause_status_o")
        self.implied_var_o = WireVector(bitwidth = var_bits, name = "implied_var_o")
        self.implied_val_o = WireVector(bitwidth = 1, name = "implied_val_o")

        # INTERNAL
        self.term_vals = [
            WireVector(bitwidth = 1, name = f"term_vals_{i}")
            for i in range(clause_size)
        ]
        self.is_sat_int = [
            WireVector(bitwidth = 1, name = f"is_sat_int_{i}")
            for i in range(clause_size)
        ]
        self.unassigned_count_int = [ # this counts 0->1->3 because that's the least logic to saturate twice
            WireVector(bitwidth = 2, name = f"unassigned_count_int_{i}")
            for i in range(clause_size)
        ]

        # LOGIC

        for i in range(clause_size):
            self.term_vals[i] <<= self.var_vals_i[i] ^ self.cs_negated_i[i]

        # TODO: has_sat logic can be a bin tree (although unassigned_count can't)
        for i in range(clause_size-1):
            if i == 0:
                self.is_sat_int[i] <<= self.term_vals[i] & self.var_assigned_i[i]
                self.unassigned_count_int[i] <<= pyrtl.concat(0, ~self.var_assigned_i[i])
            else:
                self.is_sat_int[i] <<= self.is_sat_int[i-1] | (self.term_vals[i] & self.var_assigned_i[i])
                unass = ~self.var_assigned_i[i]
                old_left, old_right = pyrtl.chop(self.unassigned_count_int[i-1],1,1)
                self.unassigned_count_int[i] <<= pyrtl.concat(old_left | (old_right & unass), old_right | unass)

        with pyrtl.conditional_assignment:
            with self.is_sat_int[-1]:
                # sat
                self.clause_status_o |= 2
            with self.unassigned_count_int[-1] == 0:
                # 0 unassigned, therefore unsat
                self.clause_status_o |= 1
            with self.unassigned_count_int[-1] == 3:
                # >1 unassigned, therefore unknown
                self.clause_status_o |= 0
            with self.unassigned_count_int[-1] == 1:
                # 1 unassigned, therefore propagate/imply
                self.clause_status_o |= 3

        # TODO: do implication
        # TODO: add tests (probably in another file)
