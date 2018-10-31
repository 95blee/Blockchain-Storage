#!/bin/sh

max_mem=0;
max_threads=0;
while pgrep miner > /dev/null
do
	mem=$(ps -o size,pcpu $(pgrep miner) | grep [0-9] |  cut -d " " -f1)
	if test $mem -gt $max_mem
	then
		max_mem=$mem
	fi
	threads=$(grep Thread /proc/$(pgrep miner)/status | cut -f2)
	if test $threads -gt $max_threads
	then
		max_threads=$threads
	fi
	sleep 0.5
done
echo "Max mem $max_mem"
echo "Max threads $max_threads"
