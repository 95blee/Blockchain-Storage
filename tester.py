#!/usr/bin/python3
from subprocess import Popen
import time
import node
import plyvel
import pickle
import random
import string


# Get a random 10 character string
def get_random_str():
    return ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(10)])


for _ in range(1):
    Popen(["./miner.py"])

    time.sleep(5)

    txs_sent = {}

    blocks_to_create = 1
    saved_txs = []
    txs_per_block = 10
    tx_created = blocks_to_create * txs_per_block
    blocks_created = 0

    created = []
    ids = []
    sending_node = node.Node()
    import random, string
    print('Node sending')
    last = 1
    # Test storage as well as temporary transactions
    for i in range(1, tx_created+1):
        if i % 2 == 0:
            #Temporary transactions should be removed from the blockchain so shouldn't exist
            #tx_id = sending_node.create_and_send_tx(get_random_str(), get_random_str(), tx_type="temp", ttl=20)
            tx = sending_node.create_tx(get_random_str(), get_random_str(), tx_type="temp", ttl=20)
            sending_node.send_tx(tx)
            txs_sent[tx.tx_id] = tx
        else:
            tx = sending_node.create_tx(get_random_str(), get_random_str(), 'perm')
            sending_node.send_tx(tx)
            saved_txs.append(tx.tx_id)
            txs_sent[tx.tx_id] = tx
    blocks_created += blocks_to_create

    #Test miner summarised transactions
    #Use incrementing numbers so we can test if summarise works properly as well
    summ_start = last
    for i in range(1, tx_created+1):
        tx = sending_node.create_tx(str(last), str(last+1), 'summ')
        sending_node.send_tx(tx)
        txs_sent[tx.tx_id] = tx
        last += 1
    summ_end = last
    blocks_created += blocks_to_create

    #Test user summarised transactions
    #The ssent transactions should not exist after summarisation
    for i in range(1, tx_created+1):
        tx = sending_node.create_tx(str(last), str(last+1), 'perm')
        created.append(tx)
        sending_node.send_tx(tx)
        txs_sent[tx.tx_id] = tx
        last += 1
    #The summarised transaction should exist on the blockchain
    tx = sending_node.create_summarise_tx(created)
    sending_node.send_tx(tx)
    saved_txs.append(tx.tx_id)
    txs_sent[tx.tx_id] = tx
    blocks_created += blocks_to_create

    #Test user remove transactions
    #Removed transactions should not exist on the blockchain
    to_remove_ids = []
    for i in range(1, tx_created+1):
        tx = sending_node.create_tx(get_random_str(), get_random_str(), 'perm')
        to_remove_ids.append(tx.tx_id)
        sending_node.send_tx(tx)
        txs_sent[tx.tx_id] = tx
    blocks_created += blocks_to_create
    tx = sending_node.create_remove_tx(to_remove_ids)
    sending_node.send_tx(tx)
    saved_txs.append(tx.tx_id)
    txs_sent[tx.tx_id] = tx

    #Pad the transactions so that all the sent transactions will be mined and exist on the blockchain
    extra_transactions = 3 * blocks_to_create
    if extra_transactions:
        for i in range(extra_transactions * 9):
            tx = sending_node.create_tx(get_random_str(), get_random_str(), 'perm')
            sending_node.send_tx(tx)
            saved_txs.append(tx.tx_id)
            txs_sent[tx.tx_id] = tx
    print('Finished sending')
    sending_node.close()

    #Let the miner finish running including it's cleaning periods
    time.sleep(60)
    passed = True
    summarise_exists = False
    all_txs = []
    #Kill the miner process so other processes can access the blockchain
    Popen(["pkill", "miner"])
    time.sleep(3)
    db = plyvel.DB("/home/ben/mof-bc")
    num_blocks = 0
    #Get all the transactions that currently exist on the blockchain
    with db.iterator() as it:
        for k, v in it:
            if k == b'last':
                continue
            block = pickle.loads(v)
            all_txs.extend(block.get_block_txs())
            #Track how many blocks have been created on the blockchain
            num_blocks += 1
    db.close()

    try:
        # Add one because there is a 'root' block
        # The 'last' block is ignored
        assert(num_blocks == blocks_created + extra_transactions + 1)
    except AssertionError:
        print("Existing number of blocks does not equal number of blocks created")
        print("Expected:", blocks_created + extra_transactions + 1, 'Found:', num_blocks)
        passed = False
    for tx in all_txs:
        if tx.tx_type == 'summarised' and tx.input == str(summ_start) and tx.output == str(summ_end):
            summarise_exists = True
    # Check if a miner summarised transaction exists on the blockchain
    # summ transactions were sent and a cleaning period was allowed to run
    # So at least one summarised transaction should exist
    try:
        assert(summarise_exists)
    except AssertionError as ae:
        passed = False
        print("Miner summarised transaction does not exist on the blockchain")
    #Check all the transactions on the blockchain match the transactions that were sent
    try:
        assert(set([tx.tx_id for tx in all_txs if tx.tx_type != 'summarised']) == set(saved_txs))
    except AssertionError as ae:
        bc_ids = [tx.tx_id for tx in all_txs]
        difference = set(bc_ids) ^ set(saved_txs)
        time.sleep(1)
        #Print the difference in transactions
        for tx_id in difference:
            if tx_id in bc_ids:
                index = bc_ids.index(tx_id)
                if all_txs[index].tx_type != 'summarised':
                    # print(all_txs[index].tx_type, all_txs[index].input, all_txs[index].output, tx_id)
                    passed = False
            else:
                # print(tx_id)
                passed = False
        if not passed:
            print("===> Transactions Difference Start <===")
            for tx_id in difference:
                if tx_id in bc_ids:
                    index = bc_ids.index(tx_id)
                    if all_txs[index].tx_type != 'summarised':
                        print("On chain", all_txs[index].tx_type, '\t\t', all_txs[index].input, '\t\t', all_txs[index].output, '\t\t', tx_id)
                        passed = False
                else:
                    print("Sent", txs_sent[tx_id].tx_type, '\t\t', txs_sent[tx_id].input, '\t\t', txs_sent[tx_id].output, '\t\t', tx_id)
                    passed = False
            print("===> Transactions Difference End <===")
    Popen(['./rm_lvldb.sh'])
    if passed:
        print("All tests passed")
    else:
        print("Failed")
        break