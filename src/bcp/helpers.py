import pyrtl
from pyrtl import WireVector
from typing import Callable

# adds two values to a max of 2 levels
# 00 -> 01 -> 11
def double_saturate(in1: WireVector, in2: WireVector):
    assert in1.bitwidth == 1 or in1.bitwidth == 2
    assert in1.bitwidth == 1 or in1.bitwidth == 2
    out = WireVector(bitwidth = 2)

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

    pyrtl.concat(left1 | left2 | (right1 & right2), right1 | right2)

# given an array of input wires, create a bin tree using op to combine them
# Assumption:
#  - all wires in the input are of length k
#  - op(a,b)->c takes two wires of width k and returns a wire of width k
def create_bin_tree(self, inputs: list[WireVector], op: Callable[[WireVector, WireVector], WireVector]):
    curr_wires = inputs

    while len(curr_wires) > 1:
        new_wires = []
        for i in range(0,len(curr_wires),2):
            new_wires.append(op(curr_wires[i], curr_wires[i+1]))

        if len(curr_wires)%2 == 1:
            # if it's odd we need to carry something over
            new_wires.append(curr_wires[-1])

        curr_wires = new_wires

    return curr_wires[0]
