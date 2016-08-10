from Bio import SeqIO
import operator
import sys
import os


def formatReadsWithCounts(input_fasta, uc_parsed_out_file, output_fasta):
    seedSizes = {}

    if os.path.isfile(output_fasta):
        os.remove(output_fasta)

    print "reading uc_parsed.out file"
    nbLines = 0
    for line in open(uc_parsed_out_file):
        #line = line.rstrip()
        data = line.rstrip().split()
        size = 0

        for d in data:
            size += int(d.split("_")[1])
        seedSizes[data[0]] = size
        if nbLines % 1000000 == 0:
            print "%s lines processed" % nbLines
        nbLines +=1

    print "Done reading uc_parsed.out file"


    seeds = []

    print "\nIndexing reads"
    reads = SeqIO.index(input_fasta, "fasta")
    print "Done indexing reads"

    print "\nRenaming sequences"
    for item in sorted(seedSizes.items(), key=operator.itemgetter(1), reverse=True):
        s = reads[item[0]]

        s.id = "%s_%s" % (item[0].split("_")[0], seedSizes[item[0]])
        s.description = ""
        seeds.append(s)
        if len(seeds) == 500000:
            SeqIO.write(seeds, open(output_fasta, 'a'), 'fasta')
            seeds =[]
    print "Done renaming sequences"
    print "Completed Susccessfully"

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print "Usage: fastaA fastaB outfile"
        exit()
    formatReadsWithCounts(sys.argv[1:4])
