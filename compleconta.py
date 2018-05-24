#!/usr/bin/env python

import os, sys
from compleconta import FileIO, Annotation, EnogLists, aminoAcidIdentity, Check, MarkerGeneBlast, ncbiTaxonomyTree

# usage: compleconta.py /path/to/protein_file.faa /path/to/hmmer_results.faa.out

protein_file=sys.argv[1]
hmmer_file=sys.argv[2]

#using the FileIO class from compleconta. the enog lists+enog weights are stored in two files which are also found in compleconta/data
IOobj=FileIO.FileIO()

#function read_enog_list returns a list only if no header present (first column), or a dict additionally (all information)
all_enogs, enog_dict = IOobj.read_enog_list(IOobj.sorted_enogs_file,header=True)
curated34_list = IOobj.read_enog_list(IOobj.universal_cogs_file,header=False)

#to handle the weights, I created a EnogList class. initialized with the enog list and the dictionary
marker_set=EnogLists.EnogList(curated34_list, enog_dict)

#the genecollection contains all enogs, the sequence names associated and the sequences. assumption: inputfile = <proteins>.faa and hmmer classification results in <proteins>.faa.out, same directory
gc=Annotation.GeneCollection()
gc.create_from_file(protein_file, hmmer_file)

#subset to enogs that actually are in the list - needed for AAI, speeds up cc slightly
gc_subset=gc.subset(curated34_list)


aai=aminoAcidIdentity.aai_check(0.9,gc_subset)
completeness, contamination=Check.check_genome_cc_weighted(marker_set,gc.get_profile())

data_dir=IOobj.get_data_dir()

database_dir=data_dir+"/databases"

taxid_list, sequence_ids, enog_names=MarkerGeneBlast.getTaxidsFromSequences(database_dir,gc_subset)

taxonomy_dir=data_dir+"/taxonomy"

tree=ncbiTaxonomyTree.NcbiTaxonomyTree(taxonomy_dir)

lca_per_sequence=[]
nodes_per_sequence=[]
percentages_per_sequence=[]
for sub_taxids in taxid_list:
	reported_lca, nodes, percentages=tree.getLCA(sub_taxids,rank=1,majority_threshold=0.9)
	lca_per_sequence.append(reported_lca.taxid)
	nodes_per_sequence.append(nodes)
	percentages_per_sequence.append(percentages)
		

reported_lca, nodes, percentages=tree.getLCA(lca_per_sequence,rank=1,majority_threshold=0.9) #standard ranks: 0 (species), 1 (genus), ..., majority threshold 0.9


#result is a tuple containing (completeness(fraction), contamination(fraction))
print("Comp.\tCont.\tSt. Het.\tncbi_taxid\ttaxon_name\ttaxon_rank\n%.4f\t%.4f\t%.4f\t%i\t%s\t%s" %(float(completeness),float(contamination), aai, reported_lca.taxid, reported_lca.name, reported_lca.rank))

print("\nLCA path and percentage of marker genes assignment:")
print("%s" % "\t".join([nodes[i].name+" "+str(round(percentages[i],2)) for i in range(len(nodes))]))

print("\nLCA per sequence of identified marker genes:")
for i in range(len(sequence_ids)):
	taxonomy="\t".join([nodes_per_sequence[i][j].name+" "+str(round(percentages_per_sequence[i][j],2)) for j in range(len(nodes_per_sequence[i]))])
	print("%s\t%s\t%s"%(sequence_ids[i],enog_names[i],taxonomy))
