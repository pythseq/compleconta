#!/bin/env python2.7
# encoding: utf-8
# from __future__ import print_function
from __future__ import division

import os
import sys
from collections import defaultdict
from collections import Iterable
from collections import namedtuple
import logging
log = logging.getLogger(os.path.basename(__file__))
# log.disabled = True

#Source: https://github.com/frallain/NCBI_taxonomy_tree
#
#The MIT License (MIT)
#
#Copyright (c) 2016 François ALLAIN

#modified by Patrick HYDEN:
# - minor changes
# - added LCA function

def flatten(seq):
    """
    >>> flatten([1 , [2, 2], [2, [3, 3, 3]]]) 
    [1, 2, 2, 2, 3, 3, 3]
    """ 
    # flatten fonction from C:\Python26\Lib\compiler\ast.py, 
    # compiler is deprecated in py2.6
    l = []
    for elt in seq:
        t = type(elt)
        if t is tuple or t is list or t is set:
            for elt2 in flatten(elt):
                l.append(elt2)
        else:
            l.append(elt)
    return l

class NcbiTaxonomyTree(object):

    def __init__(self, taxonomy_dir):#nodes_filename=None, names_filename=None):
        """ Builds the following dictionnary from NCBI taxonomy nodes.dmp and 
        names.dmp files :
        { Taxid   : namedtuple('Node', ['name', 'rank', 'parent', 'children'] }
        https://www.biostars.org/p/13452/
        https://pythonhosted.org/ete2/tutorial/tutorial_ncbitaxonomy.html
        """

        nodes_filename=taxonomy_dir+"/nodes.dmp"
        names_filename=taxonomy_dir+"/names.dmp"

        #print(nodes_filename,names_filename)

        self.standard_ranks = stdranks = ['species','genus','family','order','class','phylum','superkingdom']
        if nodes_filename and names_filename:
            log.info("NcbiTaxonomyTree building ...")
            Node = namedtuple('Node', ['name', 'rank', 'parent', 'children'])
            taxid2name = {}
            log.debug("names.dmp parsing ...")
            with open(names_filename) as names_file:
                for line in names_file:
                    line = [elt.strip() for elt in line.split('|')]
                    #print(line)
                    if line[3] == "scientific name":
                        taxid = int(line[0])
                        taxid2name[taxid] = line[1]
            log.debug("names.dmp parsed")

            log.debug("nodes.dmp parsing ...")
            self.dic = {}
            with open(nodes_filename) as nodes_file:
                for line in nodes_file:
                    line = [elt.strip() for elt in line.split('|')][:3]
                    taxid = int(line[0])
                    parent_taxid = int(line[1])

                    if taxid in self.dic: # 18204/1308852
                        self.dic[taxid] = self.dic[taxid]._replace(rank=line[2], parent=parent_taxid)
                    else: # 1290648/1308852
                        self.dic[taxid] = Node(name=taxid2name[taxid], rank=line[2], parent=parent_taxid, children=[])
                        del taxid2name[taxid]

                    try: # 1290648/1308852
                        self.dic[parent_taxid].children.append(taxid)
                    except KeyError: # 18204/1308852
                        self.dic[parent_taxid] = Node(name=taxid2name[parent_taxid], rank=None, parent=None, children=[taxid])
                        del taxid2name[parent_taxid]

            log.debug("nodes.dmp parsed")
            # to avoid infinite loop
            root_children = self.dic[1].children
            root_children.remove(1)
            self.dic[1] = self.dic[1]._replace(parent=None, children=root_children)
            # print self.dic[1000565]
            log.info("NcbiTaxonomyTree built")

    def getParent(self, taxids):
        """
            >>> tree = NcbiTaxonomyTree(nodes_filename="nodes.dmp", names_filename="names.dmp")
            >>> tree.getParent([28384, 131567])
            {28384: 1, 131567: 1}
        """
        result = {}
        for taxid in taxids:
            result[taxid] = self.dic[taxid].parent
        return result

    def getRank(self, taxids):
        """
            >>> tree = NcbiTaxonomyTree(nodes_filename="nodes.dmp", names_filename="names.dmp")
            >>> tree.getRank([28384, 131567])
            {28384: 'no rank', 131567: 'no rank'}
        """
        result = {}
        for taxid in taxids:
            result[taxid] = self.dic[taxid].rank
        return result

    def getChildren(self, taxids):
        """
            >>> tree = NcbiTaxonomyTree(nodes_filename="nodes.dmp", names_filename="names.dmp")
            >>> tree.getChildren([28384, 131567])
            {28384: [2387, 2673, 31896, 36549, 81077], 131567: [2, 2157, 2759]}
        """
        result = {}
        for taxid in taxids:
            result[taxid] = self.dic[taxid].children
        return result

    def getName(self, taxids):
        """
            >>> tree = NcbiTaxonomyTree(nodes_filename="nodes.dmp", names_filename="names.dmp")
            >>> tree.getName([28384, 131567])
            {28384: 'other sequences', 131567: 'cellular organisms'}
        """
        result = {}
        for taxid in taxids:
            result[taxid] = self.dic[taxid].name
        return result


    def getAscendantsWithRanksAndNames(self, taxids, only_std_ranks=False):
        """ 
            >>> tree = NcbiTaxonomyTree(nodes_filename="nodes.dmp", names_filename="names.dmp")
            >>> tree.getAscendantsWithRanksAndNames([1,562]) # doctest: +NORMALIZE_WHITESPACE
            {1: [Node(taxid=1, rank='no rank', name='root')],
             562: [Node(taxid=562, rank='species', name='Escherichia coli'),
              Node(taxid=561, rank='genus', name='Escherichia'),
              Node(taxid=543, rank='family', name='Enterobacteriaceae'),
              Node(taxid=91347, rank='order', name='Enterobacteriales'),
              Node(taxid=1236, rank='class', name='Gammaproteobacteria'),
              Node(taxid=1224, rank='phylum', name='Proteobacteria'),
              Node(taxid=2, rank='superkingdom', name='Bacteria'),
              Node(taxid=131567, rank='no rank', name='cellular organisms'),
              Node(taxid=1, rank='no rank', name='root')]}
            >>> tree.getAscendantsWithRanksAndNames([562], only_std_ranks=True) # doctest: +NORMALIZE_WHITESPACE
            {562: [Node(taxid=562, rank='species', name='Escherichia coli'),
              Node(taxid=561, rank='genus', name='Escherichia'),
              Node(taxid=543, rank='family', name='Enterobacteriaceae'),
              Node(taxid=91347, rank='order', name='Enterobacteriales'),
              Node(taxid=1236, rank='class', name='Gammaproteobacteria'),
              Node(taxid=1224, rank='phylum', name='Proteobacteria'),
              Node(taxid=2, rank='superkingdom', name='Bacteria')]}
        """
        def _getAscendantsWithRanksAndNames(taxid, only_std_ranks):
            Node = namedtuple('Node', ['taxid', 'rank', 'name'])
            lineage = [Node(taxid=taxid, 
                                rank=self.dic[taxid].rank, 
                                name=self.dic[taxid].name)]
            while self.dic[taxid].parent != None:
                taxid = self.dic[taxid].parent
                lineage.append(Node(taxid=taxid, 
                                        rank=self.dic[taxid].rank, 
                                        name=self.dic[taxid].name))
            if only_std_ranks:
                std_lineage = [lvl for lvl in lineage if lvl.rank in self.standard_ranks]
                lastlevel = 0
                if lineage[lastlevel].rank == 'no rank':
                    std_lineage.insert(0, lineage[lastlevel])
                lineage = std_lineage
            return lineage

        result = {}
        for taxid in taxids:
            result[taxid] = _getAscendantsWithRanksAndNames(taxid, only_std_ranks)
        return result

    def _getDescendants(self, taxid):
        """ 
            >>> tree = NcbiTaxonomyTree(nodes_filename="nodes.dmp", names_filename="names.dmp")
            >>> tree._getDescendants(208962) # doctest: +NORMALIZE_WHITESPACE
            [208962, 502347, 550692, 550693, 909209, 910238, 1115511, 1440052]
        """
        children = self.dic[taxid].children
        if children:
            result = [ self._getDescendants(child) for child in children] 
            result.insert(0, taxid)
        else:
            result = taxid
        return result

    def getDescendants(self, taxids): 
        """ Returns all the descendant taxids from a branch/clade 
            of a list of taxids : all nodes (leaves or not) of the 
            tree are returned including the original one.

            >>> tree = NcbiTaxonomyTree(nodes_filename="nodes.dmp", names_filename="names.dmp")
            >>> taxid2descendants = tree.getDescendants([208962,566])
            >>> taxid2descendants == {566: [566, 1115515], 208962: [208962, 502347, 550692, 550693, 909209, 910238, 1115511, 1440052]}
            True
        """
        result = {}
        for taxid in taxids:
            result[taxid] = flatten(self._getDescendants(taxid))
        return result

    def getDescendantsWithRanksAndNames(self, taxids):
        """ Returns the ordered list of the descendants with their respective ranks and names for a LIST of taxids.

            >>> tree = NcbiTaxonomyTree(nodes_filename="nodes.dmp", names_filename="names.dmp")
            >>> taxid2descendants = tree.getDescendantsWithRanksAndNames([566]) # doctest: +NORMALIZE_WHITESPACE
            >>> taxid2descendants[566][1].taxid 
            1115515
            >>> taxid2descendants[566][1].rank 
            'no rank'
            >>> taxid2descendants[566][1].name 
            'Escherichia vulneris NBRC 102420'
        """
        Node = namedtuple('Node', ['taxid', 'rank', 'name'])
        result = {}
        for taxid in taxids:
            result[taxid] = [Node(taxid=descendant, 
                                rank=self.dic[descendant].rank, 
                                name=self.dic[descendant].name) 
                    for descendant in self._getDescendants(taxid)] 
        return result

    def getLeaves(self, taxid): 
        """ Returns all the descendant taxids that are leaves of the tree from 
            a branch/clade determined by ONE taxid.

            >>> tree = NcbiTaxonomyTree(nodes_filename="nodes.dmp", names_filename="names.dmp")
            >>> taxids_leaves_entire_tree = tree.getLeaves(1)
            >>> len(taxids_leaves_entire_tree)
            1184218
            >>> taxids_leaves_escherichia_genus = tree.getLeaves(561)
            >>> len(taxids_leaves_escherichia_genus)
            3382
        """
        def _getLeaves(taxid):
            children = self.dic[taxid].children
            result = [_getLeaves(child) for child in children] if children else taxid
            return result
        result = _getLeaves(taxid)

        if not isinstance(result,Iterable): # In case of the taxid has no child
            result = [result]
        else:
            result = flatten(result)
        return result

    def getLeavesWithRanksAndNames(self, taxid): 
        """ Returns all the descendant taxids that are leaves of the tree from 
            a branch/clade determined by ONE taxid.

            >>> tree = NcbiTaxonomyTree(nodes_filename="nodes.dmp", names_filename="names.dmp")
            >>> taxids_leaves_entire_tree = tree.getLeavesWithRanksAndNames(561)
            >>> taxids_leaves_entire_tree[0]
            Node(taxid=1266749, rank='no rank', name='Escherichia coli B1C1')
        """
        Node = namedtuple('Node', ['taxid', 'rank', 'name'])                            
        result = [Node(taxid=leaf, 
                        rank=self.dic[leaf].rank, 
                        name=self.dic[leaf].name) 
                    for leaf in self.getLeaves(taxid)] 
        return result

    def getTaxidsAtRank(self, rank):
        """ Returns all the taxids that are at a specified rank : 
            standard ranks : species, genus, family, order, class, phylum,
                superkingdom.
            non-standard ranks : forma, varietas, subspecies, species group, 
                subtribe, tribe, subclass, kingdom.

            >>> tree = NcbiTaxonomyTree(nodes_filename="nodes.dmp", names_filename="names.dmp")
            >>> tree.getTaxidsAtRank('superkingdom')
            [2, 2157, 2759, 10239, 12884]
        """ 
        return [taxid for taxid,node in self.dic.iteritems() if node.rank == rank]

    def preorderTraversal(self, taxid, only_leaves):
        """ Prefix (Preorder) visit of the tree
            https://en.wikipedia.org/wiki/Tree_traversal
        """
        if only_leaves:
            def _preorderTraversal(taxid):
                children = self.dic[taxid].children
                result = [_preorderTraversal(child) for child in children] if children else taxid
                return result
        else:
            def _preorderTraversal(taxid):
                children = self.dic[taxid].children
                if children:
                    result = ([_preorderTraversal(child) for child in children] , taxid )
                else:
                    result = taxid
                return result
        return _preorderTraversal(taxid)


    def getLCA(self, taxids, rank=1, majority_threshold=0.9):
        """ Function to get LCA to a lowest possible rank as specified with a majority rule threshold as specified -
        the complete path down to lowest rank is still processed """
        
        rank=min(abs(rank),len(self.standard_ranks))
        selected_rank=self.standard_ranks[rank]

        all_paths=[]
        max_len=0

        for result in taxids:
            taxid=int(result)

            path=self.getAscendantsWithRanksAndNames([taxid],only_std_ranks=True)[taxid]
            path_as_list=[]
            for node in path[::-1]: #::-1 --> reversed order of list (advanced splicing)
                if not selected_rank == "species" and node.rank=="species": 	#some taxons apparently leave out other standard_ranks and jump forward to species, so in rare cases species level could be
                    break							#reported although they are not selected.
                path_as_list.append(node)
                if node.rank==selected_rank:
                    break
            max_len=max(len(path_as_list),max_len)
            all_paths.append(path_as_list)

        Node = namedtuple('Node', ['taxid', 'rank', 'name'])
        root_node=Node(taxid=1, rank='no rank', name='root')
        lca=root_node #if no taxid is provided --> root

        max_len=len(self.standard_ranks)-rank
        return_nodes=[]
        return_percentages=[]
        size=len(all_paths)
        for i in range(0,max_len):
            tmp_dict={}
            for j in range(0,size):
                try:
                    tmp_dict[all_paths[j][i]]=tmp_dict.get(all_paths[j][i],0)+1
                except IndexError:
                    #print("WARNING: not all paths equally long")
                    pass
            
            try:
                m_node=max(tmp_dict, key=tmp_dict.get)
            except ValueError: #if dict remains empty
                break
            m_frac = float(tmp_dict[m_node])/size
            if m_frac >= majority_threshold:
                lca = m_node
            return_nodes.append(m_node)
            return_percentages.append(m_frac)

        if lca.taxid==2: #so far only bacteria are in database. if superkingdom == bacteria, we can not exclude it is something different (e.g. archaea)
            lca=root_node
                
        return lca, return_nodes, return_percentages
        

if __name__ == "__main__":

    log.disabled = True
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(module)-8s l.%(lineno)-3d : %(message)s')
    steam_handler = logging.StreamHandler(sys.stdout)
    steam_handler.setLevel(logging.DEBUG)
    formatter2 = logging.Formatter('%(asctime)s %(levelname)-8s l.%(lineno)-3d : %(message)s')
    steam_handler.setFormatter(formatter2)
    log.addHandler(steam_handler)

    import tarfile
    with tarfile.open("names+nodes_test.tar.gz", 'r:gz') as tfile:
        tfile.extractall('.')

    import doctest
    doctest.testmod(verbose=True)

    
