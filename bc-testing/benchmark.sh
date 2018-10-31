#!/bin/sh

#############################################################
# Test the performance of the different configurations of   #
# the storage flexible blockchain with different parameters #
#############################################################

for num_txs in 50000 #150000 375000 750000 1500000
do
	echo "=====> BEGIN NEW TEST SET <====="
	echo "=====> $num_txs transactions <====="
#	echo "=====> Perm <====="
#	for i in `seq 1`
#	do
#		date | tr -s ' ' | cut -d ' ' -f4
#		time ./miner.py $num_txs bench &
#		sleep 1
#		./max_mem.sh 2>/dev/null &
#		./large_sender.py $num_txs 'perm'
#		while pgrep miner > /dev/null
#		do
#			:
#		done
#		./get_size.py
#		./iterate_db.py | grep blocks
#		./rm_lvldb.sh
#		sleep 1
#	done
#	echo "=====> 10 Temp <====="
#	for i in `seq 1`
#	do
#		date | tr -s ' ' | cut -d ' ' -f4
#		time ./miner.py $num_txs bench &
#		sleep 1
#		./max_mem.sh 2>/dev/null &
#		./large_sender.py $num_txs 'temp' 10
#		while pgrep miner > /dev/null
#		do
#			:
#		done
#		./get_size.py
#		db=`./iterate_db.py`
#		echo "$db" | grep blocks
#		txs=`echo "$db" | egrep "^[0-9]+ [0-9]+" | wc`
#		echo "$txs txs"
#		./rm_lvldb.sh
#		sleep 1
#	done
#	echo "=====> 10 Temp Combined <====="
#	for i in `seq 1`
#	do
#		date | tr -s ' ' | cut -d ' ' -f4
#		time ./miner.py $num_txs bench &
#		sleep 1
#		./max_mem.sh 2>/dev/null &
#		./large_sender.py $num_txs 'temp' 10 'True'> current_tx_sent
#		while pgrep miner > /dev/null
#		do
#			:
#		done
#		./get_size.py
#		db=`./iterate_db.py`
#		echo "$db" | grep blocks
#		txs=`echo "$db" | egrep "^[0-9]+ [0-9]+" | wc`
#		echo "$txs txs"
#		./rm_lvldb.sh
#		sleep 1
#	done
#	echo "=====> Half Temp <====="
#	for i in `seq 1`
#	do
#		date | tr -s ' ' | cut -d ' ' -f4
#		time ./miner.py $num_txs bench &
#		sleep 1
#		./max_mem.sh 2>/dev/null &
#		./large_sender.py $num_txs 'temp' 50
#		while pgrep miner > /dev/null
#		do
#			:
#		done
#		./get_size.py
#		db=`./iterate_db.py`
#		echo "$db" | grep blocks
#		txs=`echo "$db" | egrep "^[0-9]+ [0-9]+" | wc`
#		echo "$txs txs"
#		./rm_lvldb.sh
#		sleep 1
#	done
#	echo "=====> Half Temp Combined <====="
#	for i in `seq 1`
#	do
#		date | tr -s ' ' | cut -d ' ' -f4
#		time ./miner.py $num_txs bench &
#		sleep 1
#		./max_mem.sh 2>/dev/null &
#		./large_sender.py $num_txs 'temp' 50 'True'
#		while pgrep miner > /dev/null
#		do
#			:
#		done
#		./get_size.py
#		db=`./iterate_db.py`
#		echo "$db" | grep blocks
#		txs=`echo "$db" | egrep "^[0-9]+ [0-9]+" | wc`
#		echo "$txs txs"
#		./rm_lvldb.sh
#		sleep 1
#	done
#	echo "=====> All Temp <====="
#	for i in `seq 1`
#	do
#		date | tr -s ' ' | cut -d ' ' -f4
#		time ./miner.py $num_txs bench &
#		sleep 1
#		./max_mem.sh 2>/dev/null &
#		./large_sender.py $num_txs 'temp' 100
#		while pgrep miner > /dev/null
#		do
#			:
#		done
#		./get_size.py
#		db=`./iterate_db.py`
#		echo "$db" | grep blocks
#		txs=`echo "$db" | egrep "^[0-9]+ [0-9]+" | wc`
#		echo "$txs txs"
#		./rm_lvldb.sh
#		sleep 1
#	done
#	echo "=====> 10 Summ <====="
#	for i in `seq 1`
#	do
#		date | tr -s ' ' | cut -d ' ' -f4
#		time ./miner.py $num_txs bench &
#		sleep 1
#		./max_mem.sh 2>/dev/null &
#		./large_sender.py $num_txs 'summ' 10
#		while pgrep miner > /dev/null
#		do
#			:
#		done
#		./get_size.py
#		db=`./iterate_db.py`
#		echo "$db" | grep blocks
#		txs=`echo "$db" | egrep "^[0-9]+ [0-9]+" | wc`
#		echo "$txs txs"
#		extra=`echo "$db" | egrep summarise | wc`
#		echo "$extra extra txs"
#		./rm_lvldb.sh
#		sleep 1
#	done
#	echo "=====> 10 Summ Combined<====="
#	for i in `seq 1`
#	do
#		date | tr -s ' ' | cut -d ' ' -f4
#		time ./miner.py $num_txs bench &
#		sleep 1
#		./max_mem.sh 2>/dev/null &
#		./large_sender.py $num_txs 'summ' 10 "True"
#		while pgrep miner > /dev/null
#		do
#			:
#		done
#		./get_size.py
#		db=`./iterate_db.py`
#		echo "$db" | grep blocks
#		txs=`echo "$db" | egrep "^[0-9]+ [0-9]+" | wc`
#		echo "$txs txs"
#		extra=`echo "$db" | egrep summarise | wc`
#		echo "$extra extra txs"
#		./rm_lvldb.sh
#		sleep 1
#	done
#	echo "=====> Half Summ <====="
#	for i in `seq 1`
#	do
#		date | tr -s ' ' | cut -d ' ' -f4
#		time ./miner.py $num_txs bench &
#		sleep 1
#		./max_mem.sh 2>/dev/null &
#		./large_sender.py $num_txs 'summ' 50
#		while pgrep miner > /dev/null
#		do
#			:
#		done
#		./get_size.py
#		db=`./iterate_db.py`
#		echo "$db" | grep blocks
#		txs=`echo "$db" | egrep "^[0-9]+ [0-9]+" | wc`
#		echo "$txs txs"
#		extra=`echo "$db" | egrep summarise | wc`
#		echo "$extra extra txs"
#		./rm_lvldb.sh
#		sleep 1
#	done
#	echo "=====> Half Summ Combined<====="
#	for i in `seq 1`
#	do
#		date | tr -s ' ' | cut -d ' ' -f4
#		time ./miner.py $num_txs bench &
#		sleep 1
#		./max_mem.sh 2>/dev/null &
#		./large_sender.py $num_txs 'summ' 50 "True"
#		while pgrep miner > /dev/null
#		do
#			:
#		done
#		./get_size.py
#		db=`./iterate_db.py`
#		echo "$db" | grep blocks
#		txs=`echo "$db" | egrep "^[0-9]+ [0-9]+" | wc`
#		echo "$txs txs"
#		extra=`echo "$db" | egrep summarise | wc`
#		echo "$extra extra txs"
#		./rm_lvldb.sh
#		sleep 1
#	done
#	echo "=====> All Summ <====="
#	for i in `seq 1`
#	do
#		date | tr -s ' ' | cut -d ' ' -f4
#		time ./miner.py $num_txs bench &
#		sleep 1
#		./max_mem.sh 2>/dev/null &
#		./large_sender.py $num_txs 'summ' 100
#		while pgrep miner > /dev/null
#		do
#			:
#		done
#		./get_size.py
#		db=`./iterate_db.py`
#		echo "$db" | grep blocks
#		txs=`echo "$db" | egrep "^[0-9]+ [0-9]+" | wc`
#		echo "$txs txs"
#		extra=`echo "$db" | egrep summarise | wc`
#		echo "$extra extra txs"
#		./rm_lvldb.sh
#		sleep 1
#	done
#	echo "=====> Remove 100 <====="
#	for i in `seq 1`
#	do
#		date | tr -s ' ' | cut -d ' ' -f4
#		time ./miner.py $num_txs bench &
#		sleep 1
#		./max_mem.sh 2>/dev/null &
#		./large_sender.py $num_txs 'remove' 100 100
#		while pgrep miner > /dev/null
#		do
#			:
#		done
#		./get_size.py
#		db=`./iterate_db.py`
#		echo "$db" | grep blocks
#		txs=`echo "$db" | egrep "perm|remove" | wc`
#		echo "$txs txs"
#		./rm_lvldb.sh
#		sleep 1
#	done
#	echo "=====> Remove 1000 <====="
#	for i in `seq 1`
#	do
#		date | tr -s ' ' | cut -d ' ' -f4
#		time ./miner.py $num_txs bench &
#		sleep 1
#		./max_mem.sh 2>/dev/null &
#		./large_sender.py $num_txs 'remove' 100 1000
#		while pgrep miner > /dev/null
#		do
#			:
#		done
#		./get_size.py
#		db=`./iterate_db.py`
#		echo "$db" | grep blocks
#		txs=`echo "$db" | egrep "^[0-9]+ [0-9]+" | wc`
#		echo "$txs txs"
#		./rm_lvldb.sh
#		sleep 1
#	done
	echo "=====> Summ 100 <====="
	for i in `seq 1`
	do
		date | tr -s ' ' | cut -d ' ' -f4
		time ./miner.py $num_txs bench &
		sleep 1
		./max_mem.sh 2>/dev/null &
		./large_sender.py $num_txs 'summarise' 100 100
		while pgrep miner > /dev/null
		do
			:
		done
		./get_size.py
		db=`./iterate_db.py`
		echo "$db" | grep blocks
		txs=`echo "$db" | egrep "^[0-9]+ [0-9]+" | wc`
		echo "$txs txs"
		./rm_lvldb.sh
		sleep 1
	done
#	echo "=====> Summ 1000 <====="
#	for i in `seq 1`
#	do
#		date | tr -s ' ' | cut -d ' ' -f4
#		time ./miner.py $num_txs bench &
#		sleep 1
#		./max_mem.sh 2>/dev/null &
#		./large_sender.py $num_txs 'summarise' 1000 100
#		while pgrep miner > /dev/null
#		do
#			:
#		done
#		./get_size.py
#		db=`./iterate_db.py`
#		echo "$db" | grep blocks
#		txs=`echo "$db" | egrep "^[0-9]+ [0-9]+" | wc`
#		echo "$txs txs"
#		./rm_lvldb.sh
#		sleep 1
#	done
#	echo "=====> Remove 1000 - 10% <====="
#	for i in `seq 1`
#	do
#		date | tr -s ' ' | cut -d ' ' -f4
#		time ./miner.py $num_txs bench &
#		sleep 1
#		./max_mem.sh 2>/dev/null &
#		./large_sender.py $num_txs 'remove' 10 1000
#		while pgrep miner > /dev/null
#		do
#			:
#		done
#		./get_size.py
#		db=`./iterate_db.py`
#		echo "$db" | grep blocks
#		txs=`echo "$db" | egrep "^[0-9]+ [0-9]+" | wc`
#		echo "$txs txs"
#		#./rm_lvldb.sh
#		sleep 1
#	done
#	echo "=====> Summ 1000 - 10% <====="
#	for i in `seq 1`
#	do
#		date | tr -s ' ' | cut -d ' ' -f4
#		time ./miner.py $num_txs bench &
#		sleep 1
#		./max_mem.sh 2>/dev/null &
#		./large_sender.py $num_txs 'summarise' 10 1000
#		while pgrep miner > /dev/null
#		do
#			:
#		done
#		./get_size.py
#		db=`./iterate_db.py`
#		echo "$db" | grep blocks
#		txs=`echo "$db" | egrep "^[0-9]+ [0-9]+" | wc`
#		echo "$txs txs"
#		./rm_lvldb.sh
#		sleep 1
#	done
#	echo "=====> Remove 100 - 10% <====="
#	for i in `seq 1`
#	do
#		date | tr -s ' ' | cut -d ' ' -f4
#		time ./miner.py $num_txs bench &
#		sleep 1
#		./max_mem.sh 2>/dev/null &
#		./large_sender.py $num_txs 'remove' 10 100
#		while pgrep miner > /dev/null
#		do
#			:
#		done
#		./get_size.py
#		db=`./iterate_db.py`
#		echo "$db" | grep blocks
#		txs=`echo "$db" | egrep "^[0-9]+ [0-9]+" | wc`
#		echo "$txs txs"
#		./rm_lvldb.sh
#		sleep 1
#	done
#	echo "=====> Summ 100 - 10% <====="
#	for i in `seq 1`
#	do
#		date | tr -s ' ' | cut -d ' ' -f4
#		time ./miner.py $num_txs bench &
#		sleep 1
#		./max_mem.sh 2>/dev/null &
#		./large_sender.py $num_txs 'summarise' 10 100
#		while pgrep miner > /dev/null
#		do
#			:
#		done
#		./get_size.py
#		db=`./iterate_db.py`
#		echo "$db" | grep blocks
#		txs=`echo "$db" | egrep "^[0-9]+ [0-9]+" | wc`
#		echo "$txs txs"
#		./rm_lvldb.sh
#		sleep 1
#	done
	echo "=====> END TEST SET <====="
done