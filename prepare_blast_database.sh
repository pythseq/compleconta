#!/bin/bash

tmpdir=/tmp/bactNOG
enog_list=/apps/compleconta/0.1/data/curated_34_enogs.txt

target_dir=$(pwd)/data/databases
mkdir -p $target_dir $tmpdir

cd $tmpdir

tar -xf /mirror/eggnog/eggnog_4.5/data/bactNOG/bactNOG.raw_algs.tar.gz -C .

module load ncbiblastplus

for enog in $(less $enog_list); do
	cp bactNOG_raw_algs/*"."$enog"."* $enog".fa"
	sed 's/\..*$/\t/;s/^>/\t>/;' $enog".fa" | tr -d '\n\-' | tr "\t" "\n" > $target_dir/$enog".fa"
	makeblastdb -in $target_dir/$enog".fa" -dbtype prot 
done