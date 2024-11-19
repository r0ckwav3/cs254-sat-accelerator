import pyrtl
from pyrtl import WireVector
from .helpers import *

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
        atom_vals = [ # values of variables + if they're negated
            WireVector(bitwidth = 1, name = f"atom_vals_{i}")
            for i in range(clause_size)
        ]
        unassigned = [ # negation of var_assigned_i
            WireVector(bitwidth = 1, name = f"unassigned_{i}")
            for i in range(clause_size)
        ]
        unassigned_masked_vars = [ # the variable id if it's unassigned and 0 otherwise
            WireVector(bitwidth = var_bits, name = f"unassigned_masked_vars_{i}")
            for i in range(clause_size)
        ]
        unassigned_masked_negs = [ # the variable id if it's unassigned and 0 otherwise
            WireVector(bitwidth = var_bits, name = f"unassigned_masked_negs_{i}")
            for i in range(clause_size)
        ]

        is_sat = WireVector(bitwidth = 1, name = "is_sat")
        unassigned_count = WireVector(bitwidth = 2, name = "unassigned_count") # either 0, 1 or 3, see double_saturate
        unassigned_var = WireVector(bitwidth = var_bits, name = "unassigned_var")
        unassigned_neg = WireVector(bitwidth = 1, name = "unassigned_neg")

        # LOGIC

        # piping memory addresses around
        self.cs_addr_o <<= self.clause_id_i
        for i in range(clause_size):
            self.va_addrs_o[i] <<= self.cs_vars_i[i]

        # resolve logic
        for i in range(clause_size):
            atom_vals[i] <<= (self.var_vals_i[i] ^ self.cs_negated_i[i]) & self.var_assigned_i[i]
            unassigned[i] <<= ~self.var_assigned_i[i]
            unassigned_masked_vars[i] <<= self.cs_vars_i[i] & unassigned[i].sign_extended(var_bits)
            unassigned_masked_negs[i] <<= self.cs_negated_i[i] & unassigned[i]

        is_sat <<= create_bin_tree(atom_vals, lambda a, b: a|b)
        unassigned_count <<= create_bin_tree(unassigned, double_saturate)
        # we only care about unassigned_var when there's exactly one unassigned variable, so or works fine to extract it
        unassigned_var <<= create_bin_tree(unassigned_masked_vars, lambda a, b: a|b)
        unassigned_neg <<= create_bin_tree(unassigned_masked_negs, lambda a, b: a|b)

        with pyrtl.conditional_assignment:
            with is_sat:
                # sat
                self.clause_status_o |= 2
            with unassigned_count == 0:
                # 0 unassigned, therefore unsat
                self.clause_status_o |= 1
            with unassigned_count == 3:
                # >1 unassigned, therefore unknown
                self.clause_status_o |= 0
            with unassigned_count == 1:
                # 1 unassigned, therefore propagate/imply
                self.clause_status_o |= 3
                self.implied_var_o |= unassigned_var
                self.implied_val_o |= ~unassigned_neg
