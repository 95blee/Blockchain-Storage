#!/bin/sh
while pgrep time_temp >/dev/null
do
	clear
	date | tr -s ' ' | cut -d ' ' -f4
	tail -n4 $1
	tail -n2 current_tx_sent
	echo
	grep Thread /proc/$(pgrep miner)/status 
	sleep 2
	done
sleep 5
clear
cat $1

