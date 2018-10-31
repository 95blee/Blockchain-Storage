#!/usr/bin/python3
"""This module contains the classes and relevant methods for blocks.

Methods for block creation and manipulation are available in this module,
including block creation, traversal of the merkle tree of mined blocks,
removal of transactions stored in mined blocks and verification of creator
of transactions when a user sends remove or summarise transactions.

Classes:
    Block: Represents blocks in a blockchain.
"""

import hashlib
import threading
import time
from Crypto.Cipher import AES
import transaction


class _TreeNode:
    """The class representing a node in the merkle tree for blocks.

    The methods available relate to manipulation of the node's children
    including checking, retrieval and removal of children.
    """
    def __init__(self, children):
        self.children = children
        for child in children:
            # If the child is a transaction object, use the transaction id as data
            if isinstance(child, transaction.Transaction):
                self.data = child.tx_id
            else:
                hash_algo = hashlib.sha256()
                hash_algo.update(child.data.encode('utf-8'))
                self.data = hash_algo.hexdigest()

    def has_children(self):
        """Check if the tree node has children"""
        try:
            return len(self.children)
        # If the node has no children, it's children variable is set to None
        # and calling len() on NoneType throws a TypeError so if this is caught
        # then the node has no children
        except TypeError:
            return False

    def child_is_tx(self):
        """Check if the node's child is a transaction object"""
        return isinstance(self.children[0], transaction.Transaction)

    def get_tx_child(self):
        """Get the transaction stored as the child of this node"""
        return self.children[0]

    def remove_children(self):
        """Remove the children from this node"""
        self.children = None


class _MerkleTree:
    """The merkle tree of transactions that all blocks contain.

    Any method that involves manipulation of transactions existing on the
    blockchain will be a part of this class, including retrieval and removal
    of transactions. Verification of the creator of any transaction is also
    handled in this class.
    """
    def __init__(self, txs):
        if not txs:
            self.root = 'root'
            return
        self.root = _MerkleTree.__create(txs)

    @staticmethod
    def __create(txs):
        """Create the merkle tree by recursively hashing leaves in the tree"""
        current_level = []
        for tx in txs:
            current_level.append(_TreeNode([tx]))
        while len(current_level) > 1:
            next_level = []
            curr_iter = iter(current_level)
            for ele in curr_iter:
                children = [ele]
                try:
                    # Get the next element as well if there is one available
                    # This creates one node from two
                    ele_next = next(curr_iter)
                    children.append(ele_next)
                except StopIteration:
                    pass
                next_level.append(_TreeNode(children))
            current_level = next_level
        return current_level[0]

    def clean_tree(self):
        """Remove any non grandparent nodes from the merkle tree"""
        to_visit = [self.root]
        # Make a list of all of the nodes in the merkle tree
        for node in to_visit:
            if node.has_children() and not node.child_is_tx():
                to_visit.extend(node.children)
        # Go through the node list backwards (go up the tree from the leaves)
        # For each node, if the node's children have no children, then the
        # node can remove it's children
        # We go up the tree so that higher levels can remove lower level nodes
        # if they become leaves after removing their children
        for node in to_visit[-1::-1]:
            if node.has_children():
                has_grandchildren = False
                for child in node.children:
                    if isinstance(child, transaction.Transaction):
                        has_grandchildren = True
                    elif child.has_children():
                        has_grandchildren = True
                if not has_grandchildren:
                    node.remove_children()

    def remove(self, tx_id):
        """Remove the transaction matching the given id from this merkle tree"""
        to_visit = [self.root]
        for node in to_visit:
            if node.has_children():
                if node.child_is_tx():
                    if node.get_tx_child().tx_id == tx_id:
                        node.remove_children()
                        # Remove any nodes if possible
                        self.clean_tree()
                        return
                else:
                    to_visit.extend(node.children)

    def remove_txs(self, tx_ids):
        """Remove the transactions that match the ids in the given list"""
        to_visit = [self.root]
        removed = False
        for node in to_visit:
            if node.has_children():
                if node.child_is_tx():
                    node_tx_id = node.get_tx_child().tx_id
                    if node_tx_id in tx_ids:
                        node.remove_children()
                        tx_ids.remove(node_tx_id)
                        removed = True
                        if not tx_ids:
                            break
                else:
                    to_visit.extend(node.children)
        # If a transaction was removed, try to remove further nodes from the tree
        if removed:
            self.clean_tree()
        return removed

    @staticmethod
    def verify_gv(tx, gv):
        """Verify the gv given for a transaction"""
        aes_cipher = AES.new(gv)
        gv_sig = aes_cipher.decrypt(tx.gv)
        return tx.tx_id == gv_sig.decode('utf-8')

    def in_tree(self, tx_id):
        """Check if a transaction matching the given id exists in this tree"""
        to_visit = [self.root]
        for node in to_visit:
            if node.has_children():
                if node.child_is_tx() and node.get_tx_child().tx_id == tx_id:
                    return True
                to_visit.extend(node.children)
        return False

    def get_encoded(self, encoding):
        """Get the encoded data of the merkle tree root"""
        if self.root == 'root':
            return self.root.encode(encoding)
        return self.root.data.encode(encoding)

    def get_txs(self):
        """Return a list of the transactions stored in this merkle tree"""
        if self.root == 'root':
            return []
        txs = []
        to_visit = [self.root]
        for node in to_visit:
            if node.has_children():
                if node.child_is_tx():
                    txs.append(node.get_tx_child())
                else:
                    to_visit.extend(node.children)
        return txs

    def get_tx(self, tx_id):
        """Get a single transaction matching the id from this merkle tree"""
        to_visit = [self.root]
        for node in to_visit:
            if node.has_children():
                if node.child_is_tx() and node.get_tx_child().tx_id == tx_id:
                    return node.get_tx_child()
                to_visit.extend(node.children)
        # If the transaction does not exists, return None
        return None

    def check_usr_txs(self, usr_txs, block_hash):
        """Verify transactions stored in remove or summarise transactions

        Given a list of remove or summarise transaction tuples, try to verify
        the generator verifiers given. If the verification is successful, add
        the transaction and the block hash containing the transaction to the
        list of verified transactions in the appropriate user_txs tuple.
        """
        for tx in self.get_txs():
            for _, gv_list, id_list, tx_list in usr_txs:
                if len(id_list) == len(tx_list):
                    continue
                elif len(gv_list) != len(id_list):
                    continue
                try:
                    index = id_list.index(tx.tx_id)
                    try:
                        gv = gv_list[index]
                        if _MerkleTree.verify_gv(tx, gv):
                            tx_list.append((tx, block_hash))
                    except IndexError:
                        break
                except ValueError:
                    pass

    def get_tx_ids(self):
        """Get the transaction ids of the transactions in this tree"""
        if self.root == 'root':
            return []
        ids = []
        curr_level = [self.root]
        while curr_level:
            next_level = []
            for node in curr_level:
                if node.has_children():
                    if node.child_is_tx():
                        tx = node.get_tx_child()
                        ids.append(tx.tx_id)
                    else:
                        next_level.extend(node.children)
            curr_level = next_level
        return ids

    def print_tree(self):
        """Print the merkle tree. Useful for debugging."""
        if self.root == 'root':
            return
        curr_level = [self.root]
        while curr_level:
            next_level = []
            for node in curr_level:
                print(node.data, "--", end='')
                if node.has_children():
                    if node.child_is_tx():
                        print(' tx ->', end=' ')
                        tx = node.get_tx_child()
                        print(tx.tx_type)
                    else:
                        print()
                        next_level.extend(node.children)
                else:
                    print()
            curr_level = next_level
            print()

    def print_tree_txs(self):
        """Print only the transactions stored in this tree."""
        if self.root == 'root':
            return
        curr_level = [self.root]
        while curr_level:
            next_level = []
            for node in curr_level:
                if node.has_children():
                    if node.child_is_tx():
                        tx = node.get_tx_child()
                        print(tx.input, tx.output, tx.tx_type, tx.tx_id)
                    else:
                        next_level.extend(node.children)
            curr_level = next_level


class Block:
    """The class representing blocks in a blockchain.

    This class handles block creation and block manipulation. Because mined
    transactions are stored in block merkle trees, all operations that involve
    manipulation of existing transactions on the blockchain will pass through
    block objects which then call the appropriate method in its merkle tree.

    Methods:
            set_prev_block(prev_blck_hash):
                Set the previous block hash for this block.
            calc_and_set_block_hash():
                Set the block hash for this block from block contents.
            remove_tx(id):
                Remove the transaction with the given id if it exists.
            remove_txs(list_ids):
                Remove the transactions with ids in the given list if they exist.
            get_tx(id):
                Return the transaction with the given id if it exists in this block.
            check_usr_txs(user_txs):
                Verify the generator verifiers from user_tx tuples.
            get_tx_ids():
                Return the ids of the transactions stored in this block.
            get_block_txs():
                Return the transactions stored in this block.
    """
    def __init__(self, block_tx=None):
        self.root_hash_value = []
        self.merkle_tree = None
        root_hash_calc_thread = threading.Thread(target=self.__create_merkle_tree,
                                                 args=[block_tx])
        root_hash_calc_thread.start()
        self.prev_block_hash = "root"
        # From StackOverflow https://stackoverflow.com/a/5998359
        self.timestamp = str(int(round(time.time() * 1000)))
        self.block_hash = None
        root_hash_calc_thread.join()

    def __create_merkle_tree(self, block_tx):
        """Create the merkle tree for this block given a list of transactions"""
        self.merkle_tree = _MerkleTree(block_tx)

    def set_prev_block(self, prev_block):
        """Set the previous block hash attribute of this block"""
        self.prev_block_hash = prev_block.block_hash

    def calc_and_set_block_hash(self):
        """Calculate the block hash for this block and set it for this block"""
        block_hash_algo = hashlib.sha256()
        block_hash_algo.update(self.prev_block_hash.encode('utf-8'))
        block_hash_algo.update(self.merkle_tree.get_encoded('utf-8'))
        block_hash_algo.update(self.timestamp.encode('utf-8'))
        self.block_hash = block_hash_algo.hexdigest()

    def remove_tx(self, tx_id):
        """Remove from the block's merkle tree a transaction matching the id"""
        if self.merkle_tree.root != 'root':
            self.merkle_tree.remove(tx_id)

    def remove_txs(self, tx_ids):
        """Remove from the merkle tree all transactions matching ids in the list given"""
        if self.merkle_tree.root != 'root':
            return self.merkle_tree.remove_txs(tx_ids)
        return None

    def get_tx(self, tx_id):
        """Return the transaction from the merkle tree matching the id (can return None)"""
        return self.merkle_tree.get_tx(tx_id)

    def check_usr_txs(self, usr_txs):
        """Given a list of user tx tuples, verify the generator of the
                transactions with transaction ids in the tuples."""
        if self.merkle_tree.root != 'root':
            self.merkle_tree.check_usr_txs(usr_txs,
                                           self.block_hash.encode('utf-8'))

    def get_tx_ids(self):
        """Return the transaction ids of transactions in the merkle tree"""
        return self.merkle_tree.get_tx_ids()

    def get_block_txs(self):
        """Return the transactions stored in the merkle tree"""
        return self.merkle_tree.get_txs()
