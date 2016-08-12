import sys
from Bio import SeqIO


def seedToNames(seed_fasta, names_file):
    with open(names_file,'w') as output:
        for sequence in SeqIO.parse(open(seed_fasta,'rU'), "fasta"):
            output.write("%s\t%s\n" % (sequence.id, sequence.id))
    output.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "Usage: input_seed_fasta output_names_file"
        exit()
        seedToNames(sys.argv[1], sys.argv[2])