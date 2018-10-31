#!/usr/bin/python3
"""This module gets the size of the blocks and merkle tree in the blockchain"""
import pickle
import plyvel


db = plyvel.DB("/home/ben/mof-bc")
size = 0
block_size = 0
with db.iterator() as it:
    for block_hash, pickled_block in it:
        if block_hash == b'last':
            continue
        block = pickle.loads(pickled_block)
        m_tree_length = len(pickle.dumps(block.merkle_tree))
        size += m_tree_length
        block_size += len(pickled_block)

byte_prefix = ["", "K", "M", "G"]
prefix_count = 0
while size > 1000:
    prefix_count += 1
    size /= 1000
    block_size /= 1000

magnitude = byte_prefix[prefix_count] + "B"
print("Tree: ", size, magnitude)
print("Block: ", block_size, magnitude)
