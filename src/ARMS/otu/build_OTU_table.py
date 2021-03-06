import sys
from classes.Helpers import printVerbose


# NOTE: A SEQUENCE MUST NOT APPEAR IN TWO GROUPS FILES.
def buildOTUtable(latest_groups_files, inital_samples_files, barcodes_file, out_file):
    """Given a single barcodes file with all possible \
    sample names, a list of the latest groups file(s), and a list of initial samples files \
    (mapping each original, undereplicated sequence to its sample name), builds an OTU \
    table and writes it to out_file.

    :param latest_groups_files:  A list of the latest groups files.  No sequence name may occur in more than one \
                                    groups file.
    :param inital_samples_files: A list of the inital samples files.  This should map each sequence to its parent sample.
    :param barcodes_file:       A single barcodes file listing all valid sample names.
    :param out_file:            Filepath to the output directory
    """
    print "latest_groups_files: %s " % latest_groups_files
    print "inital_samples_files: %s " % inital_samples_files
    print "barcodes_file: %s " % barcodes_file
    
    
    seq_to_sample = {}
    # read the initaial groups/samples file (from rename)
    # make a single dict from all the groups/samples files mapping seqname to group
    all_sample_names = set()
    for samples_file in inital_samples_files:
        printVerbose("Reading samples file: %s" % samples_file)

        with open(samples_file, 'r') as current_samples_file:
            for line in current_samples_file:
                name, sample = line.split()
                sample_name = sample.rstrip()
                seq_to_sample[name] = sample_name
                all_sample_names.add(sample_name)
    all_sample_names = sorted(all_sample_names)

    printVerbose("Found the following sample names:")
    printVerbose(str(all_sample_names))
    #sys.exit(0)
    
    with open(out_file, 'w') as out:
        header_line = "OTU"
        for sample in all_sample_names:
            header_line += "\t%s" % sample
        out.write(header_line + "\n")
        # GENERATE A DICTIONARY MAPPING SEQUENCE NAMES TO THE SAMPLE THEY CAME FROM
        # for each line in the latest groups files,
        for groups_file in latest_groups_files:
            with open(groups_file, 'r') as current_groups_file:
                otu = ""
                children = ""
                # read the latest groups file
                for line in current_groups_file:
                    data = line.split("\t")

                    # TODO: if line is empty... need to find the readson for this
                    if not data:
                        continue
                    # found a cluster_main
                    if len(data) == 2:
                        otu = data[0].rstrip()
                        children = data[1].rstrip()

                    # found a singleton
                    elif len(data) == 1:
                        otu = data[0].rstrip()

                    # found a blank line
                    else:
                        pass

                    # GENERATE OTU ABUNDANCE BY SAMPLE
                    # initalize a count_dict with each sample as a key and a value of 0
                    sample_counts = {}
                    for sample_name in all_sample_names:
                        sample_counts[sample_name] = 0
                    # for each item in the child list:
                    for child in children.split():
                        # my_sample = lookup that item in the dict to get its sample name
                        my_sample = seq_to_sample[child]
                        # increment the abundance in that sample
                        sample_counts[my_sample] += 1


                    # WRITE THE COUNTS TO THE OUT FILE
                    # for each sample in the barcodes list, write otu to a txt file as a single line
                    out_line = otu
                    
                    for sample_name in all_sample_names:
                        out_line += "\t%s" % sample_counts[sample_name]
                    out.write(out_line + "\n")
    out.close()
if __name__ == "__main__":
    if len(sys.argv) < 5:
        print "Usage: list_of_latest_groups_file  list_of_inital_samples_files  barcodes_file  out_file"
        exit()
    buildOTUtable(*sys.argv[1:5])
