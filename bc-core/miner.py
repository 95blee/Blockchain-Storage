#!/usr/bin/python3
"""This module provides the class and it's related methods a blockchain miner

Classes:
    Miner: The miner that is in a blockchain. Can be used for benchmarking.
"""
import sys
import threading
import socket
import pickle
import hashlib
import time
import multiprocessing.dummy
import plyvel
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
import transaction
import block
from summarise import get_summary


class Miner:
    """The class representing a miner in a blockchain.

    Miner objects will open a handle to a database (and create one if it doesn't
    already exist), open up a socket for users to connect to and receive
    transactions. Blocks are created with transactions and block transactions
    are manipulated every cleaning period depending on their types.
    Benchmarking can be performed by providing the appropriate parameters
    into the constructor of this class.

    None of the miner methods should be invoked directly.
    """
    def __init__(self, num_txs=None, block_cap=1000000, num_stored=1000,
                 post_cap_interval=10):
        self.transactions = []
        self.running_threads = []
        # Synchronisation for block creation and list of running threads
        self.create_sync_vars()
        self.blocks_created = 0
        # How many blocks can be reached before using a fixed cleaning interval
        # This can be set to zero or one to always use a fixed cleaning interval
        self.block_cap = block_cap
        # How many block hashes to store when using a fixed cleaning interval
        # More blocks = longer fixed cleaning interval but higher possibility
        # of remove succeeding
        self.n_blocks_stored = num_stored
        # The fixed cleaning interval in seconds when using a fixed interval
        self.interval_after_cap = post_cap_interval
        try:
            # Try to open an existing database first
            self.db = plyvel.DB("/home/ben/mof-bc")
            last_tuple = pickle.loads(self.db.get('last'.encode('utf-8')))
            # Get the details of the existing database
            # (last block created and number of blocks)
            if last_tuple:
                self.prev_block = pickle.loads(self.db.get(last_tuple[0]))
                self.blocks_created = last_tuple[1]
            else:
                self.blocks_created = 0
        except plyvel.Error:
            # Database doesn't exist - create a new one
            self.db = plyvel.DB("/home/ben/mof-bc", create_if_missing=True)
            self.genesis = block.Block()
            self.genesis.calc_and_set_block_hash()
            self.prev_block = self.genesis
            self.store_block(self.genesis)
        self.sock = socket.socket()
        self.start_socket()
        self.key_hash_map = {}
        self.create_new_key()
        self.prev_tx = 'first'
        self.init_optimisation_variables()
        self.tx_per_block = 10
        # Create up to 5 threads that will create new blocks from transactions
        self.num_create_block_threads = 5
        # Spin up a thread that accepts new connections from users
        self.listen_thread = threading.Thread(target=self.accept_conn)
        self.listen_thread.start()
        # Spin up a new thread that checks the number of transactions received
        # and create new blocks if there are enough transactions
        self.check_tx_thread = threading.Thread(target=self.check_num_tx)
        self.check_tx_thread.start()
        # Spin up a new thread that will run cleaning period operations
        self.cleaning_thread = threading.Thread(target=self.clean_bc)
        self.cleaning_thread.start()
        # Used to terminate the miner when benchmarking
        self.check_to_kill = False
        self.benchmark = False
        if num_txs:
            self.benchmark = True
            self.start_time = None
            self.num_blocks = num_txs / self.tx_per_block

    def create_sync_vars(self):
        """Create all the locks used for synchronisation in this thread"""
        self.create_block_lock = threading.Lock()
        # Lock for the list that stores currently running threads
        self.thread_list_lock = threading.Lock()
        # Lock for the list that stores user summarise or remove transactions
        # that have not been consumed by a cleaning period
        self.user_tx_lock = threading.Lock()
        # Lock for the list that stores transactions that need to be removed
        self.remove_tx_lock = threading.Lock()
        # Lock for the list that stores summarisable transactions
        self.summarise_tx_lock = threading.Lock()
        self.transaction_list_lock = threading.Lock()

    def init_optimisation_variables(self):
        """Create all the variables related to cleaning the blockchain."""
        self.cleaning_interval = 20  # seconds
        # how many blocks to create before increasing the cleaning interval
        self.increase_cp_block_limit = 10000
        self.cp_increase_increment = 20
        # Python time method returns number of seconds since epoch so using
        # a period in order of seconds is appropriate
        self.next_cleaning_period = time.time() + self.cleaning_interval
        # A list of tuples of transactions that need to be removed.
        # The tuples have structure (block_hash, transaction_id, remove_time)
        # This allows constant time for removing transactions
        self.to_remove = []
        # A dictionary of transaction ids to be summarised
        # The keys of the dictionary are block hashes
        # The values are lists of transaction ids
        # A dictionary is used so searching for transactions to summarise is
        # linear to the number of transactions in the dictionary otherwise
        # the runtime is too slow
        self.to_summarise = {}
        # Store the remove and summarise transactions received from nodes
        self.user_txs = [[], []]
        # A list of the last n_blocks_stored block hashes
        self.last_n_blocks = []

    def start_socket(self):
        """Start the socket that will listen for new connections"""
        self.sock.bind(('localhost', 10000))
        self.sock.listen()

    def accept_conn(self):
        """Continuously listen for and accept new connections from nodes.

        Use tcp connection because its simpler and easier to debug if there
        is an error between node and miner
        We want reliable transmission because ensuring reliability is
        outside of the scope of this project
        """
        self.connections = []
        while True:
            conn, addr = self.sock.accept()
            self.connections.append((conn, addr))
            self.get_new_key(conn)
            sock_listen_thread = threading.Thread(target=self.listen_for_tx,
                                                  args=[conn])
            sock_listen_thread.start()

    def create_new_key(self):
        """Create a new key for miner created transactions"""
        self.key = RSA.generate(1024)
        self.priv_key = self.key.exportKey('PEM')
        self.pub_key = self.key.publickey().exportKey('PEM')
        hash_algo = hashlib.sha256()
        hash_algo.update(self.pub_key)
        self.key_hash = hash_algo.hexdigest().encode('utf-8')
        self.key_hash_map[self.key_hash] = self.pub_key

    def get_new_key(self, conn):
        """Hash and store a private key received from a node"""
        key_length = conn.recv(4).decode('utf-8')
        key_length = int(key_length)
        key = conn.recv(key_length)
        hash_algo = hashlib.sha256()
        hash_algo.update(key)
        key_hash = hash_algo.hexdigest()
        self.key_hash_map[key_hash] = key

    def listen_for_tx(self, conn):
        """Listen for new transactions from connected users.

        The digital signature of the received transactions are verified.
        There is a limit on the number of transactions that will be stored in
        the list so that the RAM load is eased.
        """
        int_size = 50  # The maximum size of a transaction in number of digits
        tx_limit = 1000000
        while True:
            if len(self.transactions) <= tx_limit:
                try:
                    obj_size = conn.recv(int_size).decode('utf-8')
                    if not obj_size:
                        break
                    obj_size = int(obj_size)
                    data = conn.recv(obj_size)
                    # Continuously receive and concatenate bytes until the
                    # whole pickled object is received
                    while len(data) < obj_size:
                        bytes_remaining = obj_size - len(data)
                        data += conn.recv(bytes_remaining)
                    rcvd_tx = pickle.loads(data)  # Unpickle the received object
                    if self.verify_tx(rcvd_tx) and self.check_tx_type(rcvd_tx):
                        self.transaction_list_lock.acquire()
                        self.transactions.append(rcvd_tx)
                        self.transaction_list_lock.release()
                    if self.benchmark and not self.start_time:
                        # If we are benchmarking and this is the first
                        # transaction received, start the timer
                        self.start_time = time.time()
                except Exception:
                    # Ignore any errors
                    continue

    def verify_tx(self, tx):
        """Check the digital signature of a received transaction"""
        pub_key_hash = tx.pub_key.decode('utf-8')
        pub_key = self.key_hash_map[pub_key_hash]
        tx_hash = SHA256.new(tx.get_signature_contents())
        key = RSA.importKey(pub_key)
        verifier = PKCS1_v1_5.new(key)
        verified = verifier.verify(tx_hash, tx.sig)
        return verified

    def close(self):
        """Clean up open sockets and database handles"""
        self.sock.close()
        self.db.close()

    def store_block(self, block_to_store):
        """Store a created block in the database"""
        try:
            # Get the bytes of the block
            byte_blocks = pickle.dumps(block_to_store)
        except Exception:
            return
        with self.db.write_batch(transaction=True) as batch:
            # Write the byte blocks to the database and update the "last block"
            # object on the database. This operation is considered atomic.
            block_hash = block_to_store.block_hash.encode('utf-8')
            batch.put(block_hash, byte_blocks)
            batch.put('last'.encode('utf-8'), pickle.dumps((block_hash,
                                                            self.blocks_created)))
        return

    def wait_to_kill(self):
        """Kill the process when all the processes have completed.

        This method will only run when the miner is started with the
        benchmarking option set to true.
        """
        time.sleep(5)
        last_tx = 0
        kill_counter = 0
        while True:
            # While there aren't any more running threads or transactions that
            # need to be removed from the blockchain or any transactions that
            # need to be summarised or any user summarise or remove transactions
            # that need to be removed and either there are no more transactions
            # that are waiting to be mined or the number of transactions
            # that are waiting to be mined have not changed in the last 25
            # or so seconds.
            if not self.to_remove and not self.to_summarise \
                    and not self.user_txs[0] and not self.user_txs[1] \
                    and not self.running_threads and (not self.transactions
                                                      or kill_counter > 5):
                # If there are still transactions left then create enough
                # "filler" transactions to make up a block.
                if self.transactions:
                    tx_left = self.tx_per_block - len(self.transactions)
                    for _ in range(tx_left):
                        self.transactions.append(transaction.Transaction
                                                 (self.prev_tx, 'filler',
                                                  'filler', self.key_hash,
                                                  'perm'))
                total_time = time.time() - self.start_time
                print("Total time =", total_time)
                print("Mining finished")
                time.sleep(10)
                self.close()
                import os
                import signal
                # Kill this process
                os.kill(os.getpid(), signal.SIGKILL)
            else:
                # Remove all threads that are finished running from the list
                # that stores running threads
                self.thread_list_lock.acquire()
                self.running_threads = [thread for thread
                                        in self.running_threads
                                        if thread.isAlive()]
                self.thread_list_lock.release()
                if len(self.transactions) == last_tx:
                    kill_counter += 1
                else:
                    last_tx = len(self.transactions)
                    kill_counter = 0
                time.sleep(5)

    def create_and_append_block(self, block_tx):
        """Create a block from a list of transactions"""
        new_block = block.Block(block_tx)
        # Lock block creation so that the blocks form a consistent chain
        # Only lock a small part of the creation so that multiple blocks
        # can be created at once and a small part is synchronised
        self.create_block_lock.acquire()
        new_block.set_prev_block(self.prev_block)
        new_block.calc_and_set_block_hash()
        self.prev_block = new_block
        self.blocks_created += 1
        # If the block cap has been reached, change the cleaning interval to
        # a predefined fixed value
        if self.blocks_created > self.block_cap:
            self.cleaning_interval = self.interval_after_cap
        store_block_thread = threading.Thread(target=self.store_block,
                                              args=[new_block])
        store_block_thread.start()
        self.last_n_blocks.append(new_block.block_hash)
        if len(self.last_n_blocks) > self.n_blocks_stored:
            self.last_n_blocks = self.last_n_blocks[1:]
        store_block_thread.join()
        self.check_block_tx_types(new_block.block_hash, block_tx)
        self.create_block_lock.release()
        # If we are benchmarking and the number of blocks created is the number
        # of blocks we are expecting based off the number of transactions
        # expected, then start the thread where it waits to kill this process
        if self.benchmark and self.blocks_created >= self.num_blocks \
                and not self.check_to_kill:
            self.check_to_kill = True
            kill_thread = threading.Thread(target=self.wait_to_kill)
            kill_thread.start()

    def check_block_tx_types(self, block_hash, txs):
        """Check the types of the block transactions when a block is created.

        This method checks for any temporary or miner summarisable transactions
        in a created block. If there are any, the transaction id and block
        hash is stored by the miner so that retrieval of these transactions
        can be performed in constant time.
        """
        block_hash = block_hash.encode('utf-8')
        for tx in txs:
            if tx.tx_type == 'temp':
                remove_time = tx.ttl + time.time()
                self.to_remove.append((block_hash, tx.tx_id, remove_time))
            elif tx.tx_type == 'summ':
                self.summarise_tx_lock.acquire()
                if block_hash in self.to_summarise:
                    self.to_summarise[block_hash].append(tx.tx_id)
                else:
                    self.to_summarise[block_hash] = [tx.tx_id]
                self.summarise_tx_lock.release()

    def check_tx_type(self, tx):
        """Check if the type of a received transaction is valid"""
        valid_type = True
        if tx.tx_type == 'perm':
            pass
        elif tx.tx_type == 'temp':
            pass
        elif tx.tx_type == 'summ':
            pass
        # Check transaction validity of remove and summarise transactions
        # during a cleaning period
        elif tx.tx_type == 'remove':
            valid_type = False
            self.user_tx_lock.acquire()
            self.user_txs[1].append(tx)
            self.user_tx_lock.release()
        elif tx.tx_type == 'summarise':
            valid_type = False
            self.user_tx_lock.acquire()
            self.user_txs[1].append(tx)
            self.user_tx_lock.release()
        # If the transaction type is not an accepted type
        else:
            valid_type = False
        return valid_type

    def block_pooling(self, block_tx):
        """The method called by map to spawn multiple threads"""
        if len(block_tx) != 10:
            print("Not 10")
        self.create_and_append_block(block_tx)

    def check_num_tx(self):
        """Check the current number of transactions in the transaction list.

        Check the number of transactions waiting to be mined. If there are at
        least 10 (or however many transactions in a block), create the
        appropriate number of threads (maximum 5) to create new blocks with
        those transactions and store them in the database.
        """
        num_threads = 5
        create_block_pool = multiprocessing.dummy.Pool(num_threads)
        while True:
            if len(self.transactions) >= self.tx_per_block:
                tx = self.transactions
                last_num = 0
                tx_for_block = []
                # Create at most 5 threads for block creation. If there is
                # less than 50 transactions, the number of threads created is
                # the highest multiple of 10 in the stored transaction list
                # length (e.g. if there is 37 transactions, create 3 threads)
                threads_spawned = 5 if len(self.transactions) >= 50 \
                    else len(self.transactions) // self.tx_per_block
                for end_tx_index in range(1, threads_spawned + 1):
                    # Slice the transaction list to take the first
                    # 10 * threads_spawned number of transactions
                    # Each list of 10 transactions is added to a list of lists
                    # i.e. [[10 txs], [10 txs], [10 txs]] and the overall list
                    # is passed to the method called which takes lists of
                    # transactions as an argument. By passing one large list
                    # of lists of transactions, we can enforce the number of
                    # transactions each blocks receives is 10.
                    tx_for_block.append(tx[last_num:end_tx_index
                                           * self.tx_per_block])
                    last_num = end_tx_index * self.tx_per_block
                # Spin up new threads that runs the block_pooling method
                create_block_pool.map(self.block_pooling, tx_for_block,
                                      threads_spawned)
                self.transaction_list_lock.acquire()
                # Slice the list to have only unmined transactions
                self.transactions = self.transactions[last_num:]
                self.transaction_list_lock.release()

    def remove_txs_from_bc(self):
        """Purge the blockchain of any transactions that need to be removed."""
        self.remove_tx_lock.acquire()
        curr_time = time.time()
        # Look for any transactions that need to be removed from the blockchain
        # These transactions are all tracked in the to_remove list
        # Temporary transactions that have past their time to live, summarisable
        # transactions that have been summarised in the past cleaning period
        # or transactions stored in the merkle tree of user summarise or remove
        # transactions that have been located on the blockchain in the past
        # cleaning period
        to_clean_list = [(block_hash, tx_id) for block_hash, tx_id, remove_time
                         in self.to_remove if remove_time <= curr_time]
        # Update the to remove list to all transactions that will need to be
        # removed in the future
        self.to_remove = [remove_tuple for remove_tuple in self.to_remove
                          if remove_tuple[2] > curr_time]
        self.remove_tx_lock.release()
        if to_clean_list:
            block_hash_dict = {}
            # Combine all transactions that are stored in the same block in
            # a single list so all transactions stored in the same block that
            # need to be removed are removed in one i/o operation
            for block_hash, tx_id in to_clean_list:
                if block_hash in block_hash_dict:
                    block_hash_dict[block_hash].append(tx_id)
                else:
                    block_hash_dict[block_hash] = [tx_id]
            # Remove all removable transactions from blocks and update the db
            for block_hash, tx_id_list in block_hash_dict.items():
                pickled_block = self.db.get(block_hash)
                loaded_block = pickle.loads(pickled_block)
                loaded_block.remove_txs(tx_id_list)
                pickled_block = pickle.dumps(loaded_block)
                self.db.put(block_hash, pickled_block)

    def verify_usr_txs(self):
        """Check some blocks to verify remove or summarise transactions"""
        # Clone the list of user summarise or remove transactions that were
        # received before this cleaning period and update the list of received
        # user summarise or remove transactions so that new received
        # transactions will be queued for verification and removal next cleaning
        # period
        self.user_tx_lock.acquire()
        user_txs = self.user_txs[0].copy()
        self.user_txs[0] = self.user_txs[1]
        self.user_txs[1] = []
        self.user_tx_lock.release()
        verified_txs = []
        if user_txs:
            # Transform the list of remove or summarise transactions into tuples
            # containing relevant information for each transaction
            # (i.e. gv values, transaction ids)
            user_txs = [(tx, tx.gv_list, tx.tx_tree.get_ids(), [])
                        for tx in user_txs]
            # Only consider the transactions that provide an equal number of
            # gv values as the number of ids in the merkle tree
            user_txs = [tx_tuple for tx_tuple in user_txs if len(tx_tuple[1])
                        == len(tx_tuple[2])]
            # Check existing blocks for transactions matching the transaction
            # ids stored in the merkle tree of remove or summarise transactions
            if self.blocks_created > self.block_cap:
                last_n_blocks = self.last_n_blocks.copy()
                for block_hash in last_n_blocks:
                    pickled_block = self.db.get(block_hash.encode('utf-8'))
                    loaded_block = pickle.loads(pickled_block)
                    loaded_block.check_usr_txs(user_txs)
                verified_txs = [tx_tuple for tx_tuple in user_txs
                                if len(tx_tuple[2]) == len(tx_tuple[3])]
            else:
                # This part should be rewritten so that transactions that are
                # verified are removed from the user_txs list so that the loop
                # can early exit if all transactions are verified
                with self.db.iterator() as it:
                    for block_hash, pickled_block in it:
                        if block_hash == b'last':
                            continue
                        loaded_block = pickle.loads(pickled_block)
                        loaded_block.check_usr_txs(user_txs)
                        verified_txs.extend([tx_tuple for tx_tuple in user_txs
                                             if len(tx_tuple[2])
                                             == len(tx_tuple[3])])
                        user_txs = [tx_tuple for tx_tuple in user_txs
                                    if len(tx_tuple[2]) != len(tx_tuple[3])]
                        if not user_txs:
                            break
        for tx, _, _, tx_list in verified_txs:
            # If all of the transactions in the remove or summarise transaction
            # has been verified
            if (tx.tx_type == 'summarise' and
                    Miner.check_user_summ(tx, tx_list)) \
                    or tx.tx_type == 'remove':
                self.transaction_list_lock.acquire()
                self.transactions.append(tx)
                self.transaction_list_lock.release()
                self.remove_tx_lock.acquire()
                # Add the transaction ids from all verified transaction
                # merkle trees to the to_remove list and give them a
                # remove time of 0
                self.to_remove.extend([(block_hash, tx.tx_id, 0) for tx,
                                       block_hash in tx_list])
                self.remove_tx_lock.release()

    @staticmethod
    def check_user_summ(tx, txs):
        """Check the inputs and outputs of a verified user summarise transaction"""
        txs = [tx_found for tx_found, block_hash in txs]
        ins, outs = get_summary(txs)
        tx_in = tx.input.split(':')
        tx_out = tx.output.split(':')
        return set(ins) == set(tx_in) and set(outs) == set(tx_out)

    def summarise_current_txs(self):
        """Summarise all received miner summarisable transactions"""
        self.summarise_tx_lock.acquire()
        summarise_tx_dict = self.to_summarise.copy()
        self.to_summarise = {}
        self.summarise_tx_lock.release()
        summarise_txs = []
        for block_hash in summarise_tx_dict:
            pickled_block = self.db.get(block_hash)
            try:
                loaded_block = pickle.loads(pickled_block)
                for tx_id in summarise_tx_dict[block_hash]:
                    summarise_txs.append(loaded_block.get_tx(tx_id))
            except pickle.UnpicklingError:
                continue
        self.remove_tx_lock.acquire()
        # Track the summarisable transactions for removal next cleaning period
        for block_hash, tx_id_list in summarise_tx_dict.items():
            for tx_id in tx_id_list:
                self.to_remove.append((block_hash, tx_id, 0))  # Remove time of 0
        self.remove_tx_lock.release()
        (inputs, outputs) = get_summary(summarise_txs)
        if inputs and outputs:
            # Create a new transaction
            summarised = transaction.Transaction(self.prev_tx, ':'.join(inputs),
                                                 ':'.join(outputs),
                                                 self.key_hash, 'summarised')
            self.prev_tx = summarised.tx_id
            self.transaction_list_lock.acquire()
            self.transactions.append(summarised)
            self.transaction_list_lock.release()

    def clean_bc(self):
        """A continuously running method that will purge the blockchain.

        This method runs while the miner is active and every cleaning period it
        will remove all transactions to be removed, summarise miner summarisable
        transactions and attempt to verify received remove or user summarise
        transaction. If it is not the next cleaning period, the thread that
        this method is running on will sleep.
        """
        while True:
            # If it is the next cleaning period
            if time.time() > self.next_cleaning_period:
                # Update the next cleaning period time
                self.next_cleaning_period = time.time() + self.cleaning_interval
                if self.to_remove:
                    # Start the remove transaction thread
                    remove_tx_thread = threading.Thread(target=self.remove_txs_from_bc)
                    self.thread_list_lock.acquire()
                    self.running_threads.append(remove_tx_thread)
                    self.thread_list_lock.release()
                    remove_tx_thread.start()
                if self.user_txs:
                    self.verify_usr_txs()
                # Start the miner summarise thread
                if self.to_summarise:
                    summarise_thread = threading.Thread(target=self.summarise_current_txs)
                    self.thread_list_lock.acquire()
                    self.running_threads.append(summarise_thread)
                    self.thread_list_lock.release()
                    summarise_thread.start()
                # If the cleaning interval is still in a dynamic state, update
                # the cleaning interval to be an appropriate amount given the
                # number of blocks currently on the blockchain
                if self.increase_cp_block_limit < self.blocks_created <= self.block_cap:
                    self.cleaning_interval = self.cp_increase_increment * \
                                             self.blocks_created // self.increase_cp_block_limit
            else:
                self.thread_list_lock.acquire()
                # Remove finished threads from the running thread list
                self.running_threads = [thread for thread in
                                        self.running_threads if thread.isAlive()]
                self.thread_list_lock.release()
                # Sleep for 5% of the cleaning interval time or 1 second,
                # whichever is smaller
                sleep_time = min(1, self.cleaning_interval // 20)
                time.sleep(sleep_time)


if __name__ == "__main__":
    num_txs_received = None
    try:
        num_txs_received = int(sys.argv[1])
    except IndexError:
        exit()
    miner = Miner(num_txs_received)
