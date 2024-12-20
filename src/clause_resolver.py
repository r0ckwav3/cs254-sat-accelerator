import pyrtl
from pyrtl import WireVector
import helpers
from helpers import wirevector_list

# exposed wires:
# Inputs:
#  - cs_vars_i:    array of variables ids in this clause (from storage)
#  - cs_negated_i: array of variable negation bits for this clause
#  - var_vals_i:     values of variables (from storage)
#  - var_assigned_i: assigned bits of variables
# Outputs:
#  - clause_status_o: returned status of the clause - 0:unknown, 1:unsat, 2: sat or 3: forced variable
#  - implied_var_o:   implied variable (if status = 3)
#  - implied_val_o:   implied value (if status = 3)

class ClauseResolver:
    def __init__(self, clause_bits: int, var_bits:int, clause_size: int):
        ## IN ##
        self.cs_vars_i =      wirevector_list(var_bits, "cs_vars_i", clause_size)
        self.cs_negated_i =   wirevector_list(1, "cs_negated_i", clause_size)
        self.var_vals_i =     wirevector_list(1, "var_vals_i", clause_size)
        self.var_assigned_i = wirevector_list(1, "var_assigned_i", clause_size)

        ## OUT ##
        self.clause_status_o = WireVector(bitwidth = 2, name = "clause_status_o")
        self.implied_var_o = WireVector(bitwidth = var_bits, name = "implied_var_o")
        self.implied_val_o = WireVector(bitwidth = 1, name = "implied_val_o")

        ## INTERNAL ##
        # values of variables + if they're negated
        atom_vals = wirevector_list(1, "atom_vals", clause_size)
        # negation of var_assigned_i
        unassigned = wirevector_list(1, "unassigned", clause_size)
         # the variable id if it's unassigned and 0 otherwise
        unassigned_masked_vars = wirevector_list(var_bits, "unassigned_masked_vars", clause_size)
        # the negation bit if it's unassigned and 0 otherwise
        unassigned_masked_negs = wirevector_list(1, "unassigned_masked_negs", clause_size)

        ored_var_addrs = WireVector(bitwidth = var_bits, name = "ored_var_addrs")
        is_sat = WireVector(bitwidth = 1, name = "is_sat")
        unassigned_count = WireVector(bitwidth = 2, name = "unassigned_count") # either 0, 1 or 3, see double_saturate
        unassigned_var = WireVector(bitwidth = var_bits, name = "unassigned_var")
        unassigned_neg = WireVector(bitwidth = 1, name = "unassigned_neg")

        ## LOGIC ##
        for i in range(clause_size):
            atom_vals[i] <<= (self.var_vals_i[i] ^ self.cs_negated_i[i]) & self.var_assigned_i[i]
            # we consider 0 vars to be assigned for the purposes of implication
            unassigned[i] <<= ~(self.var_assigned_i[i] | (self.cs_vars_i[i] == 0))
            unassigned_masked_vars[i] <<= self.cs_vars_i[i] & unassigned[i].sign_extended(var_bits)
            unassigned_masked_negs[i] <<= self.cs_negated_i[i] & unassigned[i]

        ored_var_addrs <<= helpers.create_bin_tree(self.cs_vars_i, lambda a, b: a|b)
        is_sat <<= helpers.create_bin_tree(atom_vals, lambda a, b: a|b)
        unassigned_count <<= helpers.create_bin_tree(unassigned, helpers.double_saturate)
        # we only care about unassigned_var when there's exactly one unassigned variable, so or works fine to extract it
        unassigned_var <<= helpers.create_bin_tree(unassigned_masked_vars, lambda a, b: a|b)
        unassigned_neg <<= helpers.create_bin_tree(unassigned_masked_negs, lambda a, b: a|b)

        with pyrtl.conditional_assignment:
            with is_sat | (ored_var_addrs==0):
                # sat or nothing is unassigned
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
