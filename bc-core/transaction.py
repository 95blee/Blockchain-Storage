#!/usr/bin/python3
"""This module provides the class for blockchain transactions.

Classes:
    Transaction:    Blockchain transactions are represented by this class. The
                    main methods of this class are related to creation.
"""
import hashlib
import time

class Transaction:
    """Class representing transactions sent on the blockchain.

    A node will create a transaction object for every object sent.
    It handles creation of these objects, and calculation of relevant variables.
    All other manipulation is done by either the node or miner.

    Methods:
        get_signature_contents():
            Return the concatenated string of attributes used in signature
            calculation.
        set_signature(signature):
            Set the digital signature for this transaction.
        set_gv(gv):
            Set the generator verifier for this transaction.
    """
    def __init__(self, prev_id, input_data, output_data, pk, tx_type, ttl=None,
                 gv_list=None, tx_tree=None):
        # The passed in transaction type is checked so that extra fields are not
        # erroneously saved. e.g. Only if the transaction type is temp will the
        # ttl field be saved as an object variable.
        self.prev_tx_id = prev_id
        self.input = input_data
        self.output = output_data
        self.pub_key = pk  # The hashed public key of the node
        self.tx_id = self.__calc_id()
        self.tx_type = tx_type
        self.time = time.time()
        if tx_type == 'temp':
            self.ttl = ttl
        elif tx_type in ('remove', 'summarise'):
            self.gv_list = gv_list
            self.tx_tree = tx_tree
        self.sig = None
        self.gv = None

    def __calc_id(self):
        """Calculate the transaction id from the transaction contents"""
        tx_hash_algo = hashlib.sha256()
        tx_hash_algo.update(self.prev_tx_id.encode('utf-8'))
        tx_hash_algo.update(self.input.encode('utf-8'))
        tx_hash_algo.update(self.output.encode('utf-8'))
        tx_hash_algo.update(self.pub_key)
        tx_hash_algo.update(str(time.time).encode('utf-8'))
        return tx_hash_algo.hexdigest()

    def get_signature_contents(self):
        """Get a concatenated string of the relevant transaction contents.

        Concatenate the transaction contents that are used in calculating
        the digital signature
        """
        contents = ""
        contents += self.pub_key.decode('utf-8')
        contents += self.prev_tx_id
        contents += self.input
        contents += self.output
        contents += self.tx_type
        contents += str(self.gv)
        if self.tx_type == 'temp' and self.ttl:
            contents += str(self.ttl)
        elif self.tx_type == 'summarise' or self.tx_type == 'remove':
            contents += self.tx_tree.root.data
        return contents.encode('utf-8')

    def set_signature(self, sig):
        """Set the digital signature of the transaction object"""
        self.sig = sig

    def set_gv(self, gv):
        """Set the generator verifier value of this transaction object.

        This value is the transaction id encrypted with the hash of the
        node's generator verifier secret concatenated with the transaction id.
        """
        self.gv = gv
