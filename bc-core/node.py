#!/usr/bin/python3
"""This module contains the classes and methods that represent a normal user.

Classes:
    Node: Represents a non miner participant in the blockchain.
"""

import socket
import pickle
import hashlib
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
import summarise
import transaction

class Node:
    """This class represents a normal user on the blockchain.

    Methods for creating a new user, connecting to a miner and sending
    transactions are available in this class. Public/private keypair creation
    is automated and calculation of generator verifier values is handled as well.

    Methods:
        create_tx(input, output, type, ttl, gv, tree):
            Create a transaction.
        send_tx(tx):
            Send the transaction given.
        create_and_send_tx(input, output, type, ttl, gv, tree):
            Create a transaction and send it.
        sign_tx(tx):
            Digitally sign the given transaction.
        calc_gv_key(tx_id):
            Calculate the gv value for a given transaction id.
        calc_encrypted_id(tx):
            Encrypt the transaction id of the given transaction with the gv
            value and set it for the gv in the transaction.
        get_tree_and_gv_list(list_tx):
            Get the transaction id merkle tree and a list of gv values for the
            given transactions/transaction ids.
        create_summarise_tx(txs):
            Create a summarise transaction given a list of transactions.
        create_remove_tx(tx_ids):
            Create a remove transaction given a list of transaction ids.
        close():
            Close the connection to the socket.
    """
    def __init__(self, gvs='password'):
        self.sock = socket.socket()
        self.sock.connect(('localhost', 10000))
        self.key = RSA.generate(1024)
        self.priv_key = self.key.exportKey('PEM')
        self.pub_key = self.key.publickey().exportKey('PEM')
        self.signer = PKCS1_v1_5.new(self.key)
        self.send_pub_key()
        self.hash_pub_key()
        self.last_tx = 'first'
        self.gvs = gvs

    def hash_pub_key(self):
        """Calculate the SHA256 hash of the public key used by this user."""
        hash_algo = hashlib.sha256()
        hash_algo.update(self.pub_key)
        self.key_hash = hash_algo.hexdigest().encode('utf-8')

    def send_pub_key(self):
        """Send the public key to miners upon startup.

        When starting up a new user in the blockchain, send the public key to
        miners so they can also calculate the SHA256 hash of the public key
        used so that the node can send only the public key hash in transactions
        and miners will still be able to verify the digital signature in any
        transaction sent by the user.
        """
        key_length = str(len(self.pub_key))
        # Send the length of the public key to the miner so they know how many
        # bytes to expect
        while len(key_length) < 4:
            key_length = '0' + key_length
        self.sock.send(key_length.encode('utf-8'))
        self.sock.send(self.pub_key)

    def create_tx(self, input_string, output_string, tx_type="perm", ttl=None,
                  gv_list=None, tx_tree=None):
        """Create a transaction with appropriate parameters in the constructor.

        Arguments:
            input_string: The input to the transaction.
            output_string: The output of the transaction.
            tx_type: The transaction type.
            ttl: The time to live if the transaction is temporary.
            gv_list: The list of gv values if the transaction is remove or summarise.
            tx_tree: The transaction id merkle tree if the transaction is remove or summarise.
        """
        if ttl:
            tx = transaction.Transaction(self.last_tx, input_string,
                                         output_string, self.key_hash,
                                         tx_type, ttl)
        # Creating a remove or summarise transaction
        elif gv_list:
            tx = transaction.Transaction(self.last_tx, input_string,
                                         output_string, self.key_hash, tx_type,
                                         gv_list=gv_list, tx_tree=tx_tree)
        else:
            tx = transaction.Transaction(self.last_tx, input_string,
                                         output_string, self.key_hash, tx_type)
        self.calc_encrypted_id(tx)
        tx.set_signature(self.sign_tx(tx))
        return tx

    def send_tx(self, tx):
        """Send a created transaction to the connected miner"""
        pickled_tx = pickle.dumps(tx)
        pickle_size = str(len(pickled_tx))
        while len(pickle_size) < 50:
            pickle_size = '0' + pickle_size
        pickle_size = pickle_size.encode('utf-8')
        self.sock.send(pickle_size)
        self.sock.send(pickled_tx)
        self.last_tx = tx.tx_id

    def create_and_send_tx(self, input_string, output_string, tx_type="perm",
                           ttl=None, gv_list=None, tx_tree=None):
        """Create a new transaction and then immediately send it to the miner

        See create_tx for argument descriptions.
        """
        tx = self.create_tx(input_string, output_string, tx_type, ttl, gv_list,
                            tx_tree)
        self.send_tx(tx)
        return tx.tx_id

    def sign_tx(self, tx):
        """Digitally sign a created transaction with the keypair for this user"""
        tx_hash = SHA256.new(tx.get_signature_contents())
        signature = self.signer.sign(tx_hash)
        return signature

    def calc_gv_key(self, tx_id):
        """Calculate the key used to encrypt the transaction id for a transaction"""
        sha256 = hashlib.sha256()
        # The encryption key is a SHA256 hash of the gvs and the transaction
        # id of the created transaction
        sha256.update((self.gvs + tx_id).encode('UTF-8'))
        return sha256.digest()

    def calc_encrypted_id(self, tx):
        """Calculate the encrypted id for a transaction using a generated key"""
        hash_gv = self.calc_gv_key(tx.tx_id)
        aes_cipher = AES.new(hash_gv)
        encrypted_sig = aes_cipher.encrypt(tx.tx_id)
        tx.set_gv(encrypted_sig)

    def get_tree_and_gv_list(self, txs):
        """Create a merkle tree and calculate gv keys for a list of transactions

        For remove and summarise transactions, call this method to create the
        merkle tree for a list of transactions and calculate the decryption key
        used in verifying that this user is the creator of the transactions in
        the merkle tree
        """
        if isinstance(txs[0], transaction.Transaction):
            txs = [tx.tx_id for tx in txs]
        tree = summarise.get_tx_merkle(txs)
        gv_list = [self.calc_gv_key(tx) for tx in txs]
        return tree, gv_list

    def create_summarise_tx(self, txs):
        """Create a summarise transaction from a list of transaction objects"""
        (tree, gv_list) = self.get_tree_and_gv_list(txs)
        (inputs, outputs) = summarise.get_summary(txs)
        input_string = ':'.join(inputs)
        output_string = ':'.join(outputs)
        tx = self.create_tx(input_string, output_string, 'summarise',
                            gv_list=gv_list, tx_tree=tree)
        return tx

    def create_remove_tx(self, tx_ids):
        """Create a remove transaction from a list of transaction ids"""
        (tree, gv_list) = self.get_tree_and_gv_list(tx_ids)
        tx = self.create_tx('remove_tx', 'remove_tx', 'remove',
                            gv_list=gv_list, tx_tree=tree)
        return tx

    def close(self):
        """Close the connection to the miner"""
        self.sock.close()
