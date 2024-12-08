import pyrtl
import helpers
from pyrtl import WireVector, Register
from helpers import wirevector_list, connect_wire_lists
from clause_resolver import ClauseResolver
from clause_storage import ClauseStorage
from bcp import BCP

# exposed wires:
# Inputs:
#  - write_val
#  - write_enable
#  - write_level
#  - reset_level
#  - reset_enable
# Outputs:
#  - cs_addr_o:       address sent to clause storage

def get_unassignable(a, b):
    ans = WireVector(bitwidth=max(a.bitwidth, b.bitwidth))
    with pyrtl.conditional_assignment:
        with a[0:2]==0b01:
            ans |= a
        with b[0:2]==0b01:
            ans |= b
        with pyrtl.otherwise:
            ans |= 0
    return ans

def get_unassigned(a, b):
    ans = WireVector(bitwidth=max(a.bitwidth, b.bitwidth))
    with pyrtl.conditional_assignment:
        with a[0:2]==0b00:
            ans |= a
        with b[0:2]==0b00:
            ans |= b
        with pyrtl.otherwise:
            ans |= a
    return ans

class VarAssignStore:
    def __init__(self, clause_bits: int, var_bits:int, clause_size: int, name_prefix = "assign_"):
        
        ## inputs ##
        self.start = WireVector(bitwidth = 1, name = name_prefix+"start")
        self.level = WireVector(bitwidth = 1, name = name_prefix+"level")

        ## outputs ##
        #self.active = WireVector(bitwidth = 1, name = name_prefix+"active")
        self.needs_backtrack = WireVector(bitwidth = 1, name = name_prefix+"needs_backtrack")
        self.unsat = WireVector(bitwidth = 1, name = name_prefix+"unsat")
        self.sat = WireVector(bitwidth = 1, name = name_prefix+"sat")
        self.ready_bcp = WireVector(bitwidth = 1, name = name_prefix+"ready_bcp")

        ## internal variable storage ##
        self.mem = pyrtl.MemBlock(
            bitwidth = 3 + var_bits + var_bits, # 1 for assigned, 1 for val, VAR_BITS + 1 for level, var_bits for address
            addrwidth = var_bits,
            name = "Variable Memory",
            max_read_ports = var_bits * var_bits + 1,
            max_write_ports = 2
        )

        ## internal wires ##
        #self.unassignable = WireVector(bitwidth = 3 + var_bits, name = name_prefix+"unassignable")
        #self.unassigned = WireVector(bitwidth = 3 + var_bits, name = name_prefix+"unassigned")
        self.unassignable_check = WireVector(bitwidth = 3 + var_bits + var_bits, name = name_prefix+"unassignable_check")
        self.unassigned_check = WireVector(bitwidth = 3 + var_bits + var_bits, name = name_prefix+"unassigned_check")
        #self.a_state = WireVector(bitwidth = 2, name = name_prefix+"a_state")
        
        self.every_memory_value = wirevector_list(3 + var_bits + var_bits, "every_memory_value", var_bits * var_bits)
        for i in range(var_bits * var_bits):
            self.every_memory_value[i] <<= self.mem[i]
        self.unassignable_check <<= helpers.create_bin_tree(self.every_memory_value, get_unassignable)
        self.unassigned_check <<= helpers.create_bin_tree(self.every_memory_value, get_unassigned)

        with pyrtl.conditional_assignment:
            with self.start:
                # first check if any variables are unassignable
                # if so, we need to backtrack, or if we're at level 0, we're unsat
                with self.unassignable_check[0:2]==0b01:
                    with self.unassignable_check[2:11]==0b00:
                        self.ready_bcp |= 0
                        self.needs_backtrack |= 0
                        self.unsat |= 1
                        self.sat |= 0
                    with self.unassignable_check[2:11]!=0b00:
                        self.ready_bcp |= 0
                        self.needs_backtrack |= 1
                        self.unsat |= 0
                        self.sat |= 0

                # check if all variables are assigned
                # if so, return sat
                with self.unassigned_check[0:2]!=0b00:
                    self.ready_bcp |= 0
                    self.needs_backtrack |= 0
                    self.unsat |= 0
                    self.sat |= 1


                # otherwise choose any unassigned variable to assign
                with pyrtl.otherwise:
                    self.ready_bcp |= 0
                    self.needs_backtrack |= 0
                    self.unsat |= self.needs_backtrack & (self.level == 0)
                    self.sat |= 0

            with pyrtl.otherwise:
                self.ready_bcp |= 0
                self.needs_backtrack |= 0
                self.unsat |= 0
                self.sat |= 0