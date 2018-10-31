#!/usr/bin/python3
"""Send a large amount of transactions of one type. The sending can be configured

Arguments:
    1. Number of transactions to send
    2. Type of transactions to send
    3. The percentage of transactions of the certain type to send.
    4. Whether the transactions are adjacent on the merkle tree (for temporary
       and summarisable) or the frequency of a special transaction (for remove
       and summarise)
"""
import random
import string
import sys
import node


def create_random_string():
    """Create a random 2 digit string"""
    return ''.join([random.choice(string.digits) for _ in range(2)])


def create_perm_tx(send_node):
    """Create and send a permanent transaction"""
    input_string = create_random_string()
    output_string = create_random_string()
    return send_node.create_and_send_tx(input_string, output_string, 'perm')


def is_together():
    """Check if there are 4 command line arguments"""
    return len(sys.argv) > 4


tx_created = int(sys.argv[1])
send_type = sys.argv[2]
sending_node = node.Node()
if send_type != 'perm':
    percentage = int(sys.argv[3])
    cutoff = tx_created * percentage / 100
if send_type == 'perm':
    for i in range(1, tx_created + 1):
        create_perm_tx(sending_node)
elif send_type == 'temp':
    together = is_together()
    for i in range(1, tx_created + 1):
        if together:
            if i > cutoff:
                create_perm_tx(sending_node)
            else:
                ttl = random.randrange(1, 20)
                sending_node.create_and_send_tx(create_random_string(),
                                                create_random_string(), 'temp', ttl)
        else:
            if i % 100 < percentage:
                ttl = random.randrange(1, 20)
                sending_node.create_and_send_tx(create_random_string(),
                                                create_random_string(), 'temp', ttl)
            else:
                create_perm_tx(sending_node)
elif send_type == 'summ':
    together = is_together()
    last = 1
    for i in range(1, tx_created + 1):
        if together:
            if i > cutoff:
                create_perm_tx(sending_node)
            else:
                sending_node.create_and_send_tx(str(i), str(i + 1), 'summ')
        else:
            if i % 100 < percentage:
                sending_node.create_and_send_tx(str(last), str(last+1), 'summ')
                last += 1
            else:
                create_perm_tx(sending_node)
elif send_type == 'remove':
    frequency = int(sys.argv[4])
    created = []
    for i in range(1, tx_created + 1):
        tx_id = create_perm_tx(sending_node)
        if i % 100 < percentage:
            created.append(tx_id)
        if i % frequency == 0 and i > 0:
            tx = sending_node.create_remove_tx(created)
            sending_node.send_tx(tx)
            print("Sent")
            created = []
elif send_type == 'summarise':
    frequency = int(sys.argv[4])
    created = []
    last = 1
    for i in range(1, tx_created + 1):
        tx = sending_node.create_tx(str(last), str(last + 1))
        last += 1
        sending_node.send_tx(tx)
        if i % 100 < percentage:
            created.append(tx)
        if i % frequency == 0 and i > 0:
            tx = sending_node.create_summarise_tx(created)
            sending_node.send_tx(tx)
            created = []

sending_node.close()
