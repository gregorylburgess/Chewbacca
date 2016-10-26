from Bio import SeqIO
from collections import defaultdict
from dev.nast import nast_regap, locate_deltas, apply_deltas, mask_deltas, resolve_deltas, make_faa_gc_lookup, \
    get_best_hits_from_vsearch, translate_to_prot
from dev.utils import globalProtAlign

#query.fna", bold10k.fna", bold10k.faa.msa, bold10k_name_pairs.txt
def add_to_msa(input_fna, ref_fna, ref_faa_msa, name_map, outdir):

    # read MSA file to dict
    print "Reading MSA file"
    ref_msa = SeqIO.to_dict(SeqIO.parse(open(ref_faa_msa, 'r'), 'fasta'))

    print "Reading query file"
    queries = SeqIO.to_dict(SeqIO.parse(open(input_fna, 'r'), 'fasta'))

    # store the gc for each ref seq
    print "Looking up GCs and names"
    gc_lookup_map, fna_faa_map = make_faa_gc_lookup(name_map)

    # Find closest neighbors for each input sequence
    print "Finding best pairs"
    best_hits = get_best_hits_from_vsearch(input_fna, ref_fna, outdir)
    if len(best_hits) == 0:
        print "\n\n\nERROR: no matching IDs found in reference DB."
        exit()
    # Translate NA to AA
    print "Translating"
    translations = translate_to_prot(input_fna, best_hits, gc_lookup_map)

    # Regap pairwise alignment to incldue MSA template gaps
    msa_templates = []
    nast_refs = []
    nast_queries = []
    pairwise_queries = []
    cumulative_insertions = defaultdict(list)
    priority = 0

    for name in translations.keys():
        # Pairwise align query AA to ref AA
        pairwise_ref, pairwise_query = globalProtAlign(ref_msa[fna_faa_map[best_hits[name][1]]].seq.ungap('-'),
                                                       translations[name][0])[0:2]

        msa_template_ref = str(ref_msa[fna_faa_map[best_hits[name][1]]].seq)
        nast_query, nast_ref = nast_regap(msa_template_ref, pairwise_ref, pairwise_query)

        # compute the deltas between the pairwise template and the MSA template
        cumulative_insertions, local_insertions = locate_deltas(msa_template_ref, nast_ref, nast_query,
                                                                cumulative_insertions, priority)

        # replace each query's deltas with lowercase so we know to replace them later (instead of inserting gaps)
        nast_query = mask_deltas(local_insertions, nast_query)

        priority +=1
        nast_refs.append(nast_ref)
        nast_queries.append(nast_query)
        msa_templates.append(msa_template_ref)
        pairwise_queries.append(pairwise_query)

    # Resolve the global changes by sorting them within their dictionaries by priority
    cumulative_insertions = resolve_deltas(cumulative_insertions)
    print cumulative_insertions
    if len(cumulative_insertions) > 0:
        # A ruler
        ruler = (' '*4 + "*" + ' ' * 4 + "!") *60
        print apply_deltas(cumulative_insertions, ruler, '@', True)

        for i in range(len(translations)):
            print apply_deltas(cumulative_insertions, msa_templates[i], '@')
            print apply_deltas(cumulative_insertions, nast_queries[i], '@')
            print "\n"
        # insert back into msa, and update msa
    else:
        for i in range(len(translations)):
            print msa_templates[i]
            print nast_queries[i]
            print "\n"

data_dir = "/home/greg/ARMS/src/ARMS/dev/data"
add_to_msa("%s/query2.fna" % data_dir,
         "%s/bold10k.fna" % data_dir,
         "%s/bold10k.faa.msa" % data_dir,
         "%s/bold10k_name_pairs.txt" % data_dir,
         "/home/greg/ARMS/testARMS/out1_")



