import pyrtl
from pyrtl import WireVector
from typing import Callable, Sequence

## LIST HELPERS ##
def wirevector_list(bitwidth:int, name:str, length:int, wirevector_class=WireVector):
    return [
        wirevector_class(bitwidth = bitwidth, name = f"{name}_{i}")
        for i in range(length)
    ]

# connect out <<= in
def connect_wire_lists(out_wires: Sequence[WireVector], in_wires: Sequence[WireVector]):
    assert len(out_wires) == len(in_wires)
    for i in range(len(out_wires)):
        # this is to make my language server happy
        out_wire = out_wires[i]
        out_wire <<= in_wires[i]

# returns a list of [in_1, in_2...] -> [f(in_1), f(in_2)...]
def map_wires(wire_list: Sequence[WireVector], op: Callable[[WireVector], WireVector]):
    return [op(wire_list[i]) for i in range(len(wire_list))]


## BCP HELPERS ##
# adds two values to a max of 2 levels
# 00 -> 01 -> 11
def double_saturate(in1: WireVector, in2: WireVector) -> WireVector:
    assert in1.bitwidth == 1 or in1.bitwidth == 2
    assert in1.bitwidth == 1 or in1.bitwidth == 2

    if in1.bitwidth == 1:
        left1 = 0
        right1 = in1
    else:
        left1, right1 = pyrtl.chop(in1,1,1)

    if in2.bitwidth == 1:
        left2 = 0
        right2 = in2
    else:
        left2, right2 = pyrtl.chop(in2,1,1)

    return pyrtl.concat(left1 | left2 | (right1 & right2), right1 | right2)

# given an array of input wires, create a bin tree using op to combine them
# Assumption:
#  - all wires in the input are of length k
#  - op(a,b)->c takes two wires of width k and returns a wire of width k
def create_bin_tree(inputs: Sequence[WireVector], op: Callable[[WireVector, WireVector], WireVector]):
    curr_wires = inputs

    while len(curr_wires) > 1:
        new_wires = []
        for i in range(1,len(curr_wires),2):
            new_wires.append(op(curr_wires[i-1], curr_wires[i]))

        if len(curr_wires)%2 == 1:
            # if it's odd we need to carry something over
            new_wires.append(curr_wires[-1])

        curr_wires = new_wires

    return curr_wires[0]

def create_bin_tree_modified(inputs: Sequence[WireVector], op: Callable[[WireVector, WireVector, str], WireVector]):
    curr_wires = inputs

    counter = 0

    while len(curr_wires) > 1:
        counter += 1
        new_wires = []
        for i in range(1,len(curr_wires),2):
            counter += 1
            new_wires.append(op(curr_wires[i-1], curr_wires[i], f"{counter}"))

        if len(curr_wires)%2 == 1:
            # if it's odd we need to carry something over
            new_wires.append(curr_wires[-1])

        curr_wires = new_wires

    return curr_wires[0]
