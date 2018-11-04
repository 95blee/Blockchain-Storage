# Blockchain-Storage

## Licence

There is no licence associated with this code. Do with it as you see fit.

## Requirements

You need:

1. Python3
2. LevelDB
3. Plyvel
4. PyCrypto
    
## Description
    
This is the code for a basic implementation of a storage flexible blockchain written in Python. Right now, the blockchain components run off TCP instead of UDP like a blockchain normally would. This is because my thesis assumed that you should be able to receive transactions reliably and error free for the most accurate results. If you want to start up a miner instance, you can either run the miner.py script which will create a process on port 10000 with some default settings. You can tweak these settings by creating your own script that will start a create its own miner instance with something like the following:

```python
import miner

miner = Miner(your_own_settings)
```
    
You can also start a node (transaction sender) in the same way.

## !NOTE!

If you want to run this on your own computer you'll need to change some of the files so that the database is created in the correct location.
This is fairly easy to do and can be done with a single command (if on Linux):

    sed "s#/home/ben/mof-bc#new_location#"


where new\_location is the location you want to create the blockchain database.
You can also manually edit the files if that's your thing. Search and replace _"/home/ben/mof-bc"_ in the following files:

- bc-core/miner.py
- bc-testing/get_size.py
- bc-testing/iterate_db.py
- bc-testing/tester.py

## File Structure

There are only two folders with structure:

    |
    |
    |-- bc-core:
    |       |-- All of the components that make up the storage flexible blockchain
    |       |-- If you want to just run the code you likely won't have to change anything
    |       |-- miner.py
    |       |-- node.py
    |       |-- transaction.py
    |       |-- summarise.py
    |       |-- transaction.py
    |
    |
    |-- bc-testing:
            |-- All of the files used to benchmark the storage flexible blockchain
            |-- You can change some of these files to test performance of different parameter configurations
            |-- benchmark.sh        (change this if you want to test different configurations)
            |-- large_sender.py
            |-- get_size.sh
            |-- max_mem.sh
            |-- iterate_db.py
            |-- rm_lvldb.sh
            |-- tester.py           (if you have edited the core code, run this to test correctness for a very small dataset)
            
## Changing the code

If you want to work on this project, feel free to change the code however you want. You can change the type of database used; I went with leveldb because it was the easiest to install and had good enough performance.
Also, I'd recommend changing the crypto library used because PyCrypto is a dead project. Have a look at PyNaCl for a different library. Run the tester.py in bc-testing to see if it passes a very simple test.
