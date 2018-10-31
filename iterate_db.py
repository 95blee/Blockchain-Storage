#!/usr/bin/python3

import plyvel
import pickle
import sys
import time
import block
import os

ts = time.time()
db = plyvel.DB("/home/ben/mof-bc")
blocks = 0 
with db.iterator() as it:
    for k,v in it:
        if k == b'last':
            continue
        blocks += 1
        block = pickle.loads(v)
        if block.merkle_tree.root != 'root':
            block.merkle_tree.print_tree_txs()
        else:
            print(block, '-> root')
tf = time.time()
print(blocks, 'blocks')
print("Time taken", tf-ts, "seconds")
