import pyrtl
import helpers
from pyrtl import WireVector, Register
from helpers import wirevector_list, connect_wire_lists
from clause_resolver import ClauseResolver
from clause_storage import ClauseStorage
from bcp import BCP

def get_unassignable(a, b):
    ans = WireVector(bitwidth=max(a.bitwidth, b.bitwidth))
    with pyrtl.conditional_assignment:
        with (a[0]==0) & (a[1]==1):
            ans |= a
        with (b[0]==0) & (b[1]==1):
            ans |= b
        with pyrtl.otherwise:
            ans |= b
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
        self.level = WireVector(bitwidth = var_bits+1, name = name_prefix+"level")

        ## outputs ##
        #self.active = WireVector(bitwidth = 1, name = name_prefix+"active")
        self.needs_backtrack = WireVector(bitwidth = 1, name = name_prefix+"needs_backtrack")
        self.unsat = WireVector(bitwidth = 1, name = name_prefix+"unsat")
        self.sat = WireVector(bitwidth = 1, name = name_prefix+"sat")
        self.ready_bcp = WireVector(bitwidth = 1, name = name_prefix+"ready_bcp")

        ## internal variable storage ##
        self.mem = pyrtl.MemBlock(
            bitwidth = 4 + var_bits + var_bits, # 1 for assigned, 1 for val, VAR_BITS + 1 for level, var_bits for address
            addrwidth = var_bits,
            name = "Variable Memory",
            max_read_ports = 2 ** var_bits + 1 + clause_size, # oops you didn't see that!
            max_write_ports = 3,
            asynchronous=True
        )

        ## internal wires ##
        self.unassignable_check = WireVector(bitwidth = 4 + var_bits + var_bits, name = name_prefix+"unassignable_check")
        self.unassigned_check = WireVector(bitwidth = 4 + var_bits + var_bits, name = name_prefix+"unassigned_check")
        self.new_assign = WireVector(bitwidth = 4 + var_bits + var_bits, name = name_prefix+"new_assign")

        self.every_memory_value = wirevector_list(4 + var_bits + var_bits, "every_memory_value", 2 ** var_bits)
        for i in range(2 ** var_bits):
            self.every_memory_value[i] <<= self.mem[i]
        self.unassignable_check <<= helpers.create_bin_tree(self.every_memory_value, get_unassignable)
        self.unassigned_check <<= helpers.create_bin_tree(self.every_memory_value, get_unassigned)

        with pyrtl.conditional_assignment:
            with self.start:
                # first check if any variables are unassignable
                # if so, we need to backtrack, or if we're at level 0, we're unsat
                with (self.unassignable_check[0]==0)& (self.unassignable_check[1]==1):
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
                    index_bits = self.unassigned_check[11:19]
                    assign_bit = pyrtl.Const(1, bitwidth=1)
                    val_bit = pyrtl.Const(0, bitwidth=1)
                    level_bits = self.level

                    is_root = pyrtl.Const(1, bitwidth=1)

                    self.new_assign |= pyrtl.concat(is_root, index_bits, level_bits, val_bit, assign_bit)
                    self.mem[index_bits] |= self.new_assign

                    self.ready_bcp |= 1
                    self.needs_backtrack |= 0
                    self.unsat |= 0
                    self.sat |= 0

            with pyrtl.otherwise:
                # inactive
                self.ready_bcp |= 0
                self.needs_backtrack |= 0
                self.unsat |= 0
                self.sat |= 0
