import pyrtl
from pyrtl import WireVector, Register
from helpers import wirevector_list, connect_wire_lists

from clause_resolver import ClauseResolver
from clause_storage import ClauseStorage


# exposed wires:
# Inputs:
# - start_i:        send a 1 to start BCP
# - var_vals_i:     values of variables (from storage)
# - var_assigned_i: assigned bits of variables
# Outputs:
# - active_o:          is BCP currently processing
# - status_o:          0 success, 1 failure (contradiction found)
# - va_addrs_o:        addresses of variables (for storage)
# - va_write_addr_o:   address of a variable to write
# - va_write_val_o:    val of a variable to write
# - va_write_enable_o: enable bit for writing a variable

class BCP:
    def __init__(self, clause_bits: int, var_bits:int, clause_size: int, name_prefix = "bcp_"):
        ## inputs ##
        self.start_i =        WireVector(bitwidth = 1, name = name_prefix+"start_i")
        self.var_vals_i =     wirevector_list(1, name_prefix+"var_vals_i", clause_size)
        self.var_assigned_i = wirevector_list(1, name_prefix+"var_assigned_i", clause_size)

        ## outputs ##
        self.active_o =          WireVector(bitwidth = 1, name = name_prefix+"active_o")
        self.status_o =          WireVector(bitwidth = 1, name = name_prefix+"status_o")
        self.va_addrs_o =        wirevector_list(var_bits, name_prefix+"va_addrs_o", clause_size)
        self.va_write_addr_o =   WireVector(bitwidth = var_bits, name = name_prefix+"va_write_addr_o")
        self.va_write_val_o =    WireVector(bitwidth = 1, name = name_prefix+"va_write_val_o")
        self.va_write_enable_o = WireVector(bitwidth = 1, name = name_prefix+"va_write_enable_o")

        ## internal registers ##
        clause_addr = Register(bitwidth = clause_bits, name = "clause_addr") # current clause address
        max_addr    = pyrtl.Const(-1, bitwidth = clause_bits)

        active =      Register(bitwidth = 1, name = "active")
        update_made = Register(bitwidth = 1, name = "update_made") # has a variable been written this iteration

        ## internal wires ##
        iteration_finished = WireVector(bitwidth = 1, name = "iteration_finished")
        reset =              WireVector(bitwidth = 1, name = "reset") # reset to a new iteration
        writing =            WireVector(bitwidth = 1, name = "writing") # are we writing a variable this cycle
        contradiction =      WireVector(bitwidth = 1, name = "contradiction") # bcp found a contradiction

        ## substructures ##
        clause_resolver = ClauseResolver(clause_bits, var_bits, clause_size)
        self.clause_storage  = ClauseStorage(clause_bits, var_bits, clause_size)

        ## logic ##
        iteration_finished <<= (clause_addr == max_addr)
        reset <<= iteration_finished | self.start_i | contradiction

        with pyrtl.conditional_assignment:
            with reset:
                clause_addr.next |= 0
                # essentially forward writing since update_made won't update fast enough
                active.next      |= self.start_i | ((update_made | writing) & ~contradiction)
                update_made.next |= 0
            with pyrtl.otherwise:
                clause_addr.next |= clause_addr + active
                active.next      |= active
                update_made.next |= update_made | writing

        clause_resolver.clause_id_i <<= clause_addr
        # we don't use clause_resolver.cs_addr_o or va_addrs_o because we just have that info locally
        self.clause_storage.addr_i <<= clause_addr
        connect_wire_lists(clause_resolver.cs_vars_i, self.clause_storage.vars_o)
        connect_wire_lists(clause_resolver.cs_negated_i, self.clause_storage.negs_o)
        connect_wire_lists(self.va_addrs_o, self.clause_storage.vars_o)
        connect_wire_lists(clause_resolver.var_vals_i, self.var_vals_i)
        connect_wire_lists(clause_resolver.var_assigned_i, self.var_assigned_i)

        with pyrtl.conditional_assignment:
            with ~active:
                pass
            with clause_resolver.clause_status_o == 0:
                pass
            with clause_resolver.clause_status_o == 1:
                contradiction |= 1
            with clause_resolver.clause_status_o == 2:
                pass
            with clause_resolver.clause_status_o == 3:
                writing |= 1
                self.va_write_addr_o   |= clause_resolver.implied_var_o
                self.va_write_val_o    |= clause_resolver.implied_val_o
                self.va_write_enable_o |= 1

        # more forwarding type of thing so that we can don't need to stall status for a cycle
        self.active_o <<= active & ~contradiction
        self.status_o <<= contradiction
