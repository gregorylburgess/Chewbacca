from Bio import SeqIO
import sys

# Renames sequences for swarm


def renameSequences(input_fasta, count_file, outfile):
    seeds ={}
    # collect the seed names, and the children sequence names
    for line in open(count_file, 'r'):
        line = line.rstrip()
        seeds[line.split("\t")[0]] = line.split("\t")[1]

    i=0
    mySeqs=[]

    # pull the sequence data for each seed from the input fasta
    for mySeq in SeqIO.parse(input_fasta, 'fasta'):
        i+=1

        if seeds.has_key(mySeq.id):
            mySeq.id = "%i_%i" % (i, len(seeds[mySeq.id].split(" ")))
        else:
            mySeq.id = "%i_%i" % (i, 1)
        mySeqs.append(mySeq)

    # write a new fasta with only the seed sequences
    SeqIO.write(mySeqs, open(outfile, 'w'),'fasta')

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print "Usage: fastaA fastaB outfile"
        exit()
        renameSequences(sys.argv[1:4])
