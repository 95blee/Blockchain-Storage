#!/usr/bin/python3
"""This module provides methods for summarising transactions.

Methods:
    get_tx_merkle(list_transaction_ids):
        Create a SummaryMerkle object and return it
    get_summary(list_transactions):
        Determine the inputs and outputs of a summarise transaction
    get_order(list_transactions):
        Get the first n distinct bytes that will let a user determine
        the order of transactions in a summarised transaction
"""
import hashlib


class _SummaryTreeNode:
    """A node in the summary merkle tree.

    This class has no methods other than its constructor.
    """
    def __init__(self, children, is_id=False):
        self.children = children
        for child in children:
            if is_id:
                # If the child data is a transaction id
                # This is for the leaf nodes of the merkle trees and the ids
                # are the transaction ids in the given list
                self.data = child
            else:
                hash_algo = hashlib.sha256()
                hash_algo.update(child.data.encode('utf-8'))
                self.data = hash_algo.hexdigest()


class _SummaryMerkle:
    """The merkle tree that is used in user summarise and remove transactions"""
    def __init__(self, txs):
        if not txs:
            self.root = 'root'
            return
        self.root = _SummaryMerkle.__create(txs)

    @staticmethod
    def __create(txs):
        """Create the merkle tree by recursively hashing leaves in the tree"""
        current_level = []
        for tx in txs:
            current_level.append(_SummaryTreeNode([tx], True))
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
                next_level.append(_SummaryTreeNode(children))
            current_level = next_level
        return current_level[0]

    def print_tree(self):
        """Print all the nodes of the merkle tree.

        This will print the nodes of the merkle tree separated by a newline
        character. The leaves of the tree will have their data printed as well.
        Useful for debugging.
        """
        if self.root == 'root':
            return
        curr_level = [self.root]
        while curr_level:
            next_level = []
            for node in curr_level:
                if isinstance(node, _SummaryTreeNode):
                    print(node.data, "--", end='')
                    if node.children:
                        print()
                        next_level.extend(node.children)
                    else:
                        print()
                else:
                    print(node, '-- id')
            curr_level = next_level
            print()

    def get_ids(self):
        """Get the transaction ids from this merkle tree."""
        if self.root == 'root':
            return []
        ids = []
        curr_level = [self.root]
        while curr_level:
            next_level = []
            for node in curr_level:
                if isinstance(node, _SummaryTreeNode):
                    if node.children:
                        next_level.extend(node.children)
                else:
                    ids.append(node)
            curr_level = next_level
        return ids


def get_tx_merkle(txs):
    """Create the merkle tree given a list of transactions."""
    return _SummaryMerkle(txs)


def _summarise(txs):
    """Given a list of transactions, determine distinct inputs and outputs."""
    ins = set()
    outs = set()
    for tx in txs:
        for tx_input in tx.input.split(':'):
            ins.add(tx_input)
        for output in tx.output.split(':'):
            outs.add(output)
    return ins-outs, outs-ins


def get_summary(txs):
    """Summarise the given inputs and outputs and return them as lists."""
    (ins, outs) = _summarise(txs)
    return list(ins), list(outs)


def _get_only_inputs(txs):
    """Get only the inputs of a summarised list of transactions."""
    return list(_summarise(txs)[0])


def _get_starting_txs(inputs, input_dict):
    """Get the transactions that make up the distinct inputs from a list."""
    starting_txs = []
    for input_to_visit in inputs:
        starting_txs.append(input_dict[input_to_visit])
    return starting_txs


def get_order(txs):
    """Given a list of transactions, get the first n distinct bytes.

    Given a list of transactions, determine the summarised inputs and from the
    inputs, determine the order of the transactions. From the transaction
    order, return the smallest n bytes such that the first n bytes for all
    the given transactions are unique in the order of summarising."""
    inputs = _get_only_inputs(txs)
    input_dict = {}
    # Add all inputs into a dictionary where the input indexes to the
    # transaction that has that input
    for tx in txs:
        tx_ins = tx.input.split(':')
        for tx_in in tx_ins:
            input_dict[tx_in] = tx
    summ_order = []
    to_visit = _get_starting_txs(inputs, input_dict)
    for counter, tx in enumerate(to_visit):
        summ_order.append(tx)
        tx_outs = tx.output.split(':')
        for tx_out in tx_outs:
            if tx_out in input_dict:
                to_visit.insert(counter+1, input_dict[tx_out])
    unique_bytes = 1
    byte_seen = set()
    num_checked = 0
    # Get the first n distinct bytes of the id for all the given transactions
    # Iterate over the transactions taking the first n bytes of id, starting
    # with n = 1
    # If the bytes exist at the start for another transaction, increment n
    # and repeat until first n bytes for all transactions are unique
    while num_checked < len(summ_order):
        for tx in summ_order:
            tx_id = tx.tx_id
            trunc_id = tx_id[0:unique_bytes]
            if trunc_id not in byte_seen:
                byte_seen.add(trunc_id)
                num_checked += 1
            else:
                num_checked = 0
                unique_bytes += 1
                byte_seen = set()
                break
    order = []
    for tx in summ_order:
        order.append(tx.tx_id[0:unique_bytes])
    return order
