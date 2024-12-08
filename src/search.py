# PyRTL implementation to find the index of the first non-zero value in a memory block
import pyrtl

# Inputs
memory_block = pyrtl.MemBlock(bitwidth=32, addrwidth=8, name='memory_block', max_read_ports=257, max_write_ports=1)
N = pyrtl.Input(bitwidth=8, name='N')  # Size of the memory block

# Outputs
index = pyrtl.Output(bitwidth=8, name='index')

# Internal signals
found = pyrtl.Register(bitwidth=1, name='found')
current_index = pyrtl.Register(bitwidth=8, name='current_index')

# Initialize outputs and internal signals
index <<= pyrtl.Const(-1, bitwidth=8)  # Default index to -1 if no non-zero value is found
#found.next <<= pyrtl.Const(0, bitwidth=1)  # Initialize found to false

# Define logic for finding the first non-zero value
with pyrtl.conditional_assignment:
    with ~found:
        for i in range(256):  # Assuming maximum address width of 8 bits
            with current_index == i:
                with memory_block[i] != 0:
                    index <<= i
                    found.next <<= 1
                with memory_block[i] == 0:
                    current_index.next <<= current_index + 1
    with found:
        current_index.next <<= current_index
