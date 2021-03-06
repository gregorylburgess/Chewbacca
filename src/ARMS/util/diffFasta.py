import sys
from Bio import SeqIO

def diff(fastaA, fastaB, outFile, filetype):
    """Writes the difference of fastaA and fastaB to outFile.  i.e. A-B
        i.e. Write to file the records in fastaA but not fastaB.

    :param fastaA:  The first fasta file.  Preferably the larger fasta file.
    :param fastaB:  The second fasta file. Preferably the smaller fasta file.
    :param outFile: Where to write the resuling fasta to.
    :return: Filepath to the output file.
    """
    commonRecords = {}
    records = []
    i=0
    with open(outFile,'w') as out:
        for record in SeqIO.parse(open(fastaB,'r'), filetype):
            commonRecords[record.id]=""
        foundIDs = commonRecords.keys()
        for record in SeqIO.parse(open(fastaA,'r'), filetype):
            if not record.id in foundIDs:
                records.append(record)
                i += 1
                if i % 5000 == 0:
                    SeqIO.write(records, out, filetype)
                    records = []
        SeqIO.write(records, out, filetype)
    return outFile

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print "Usage: fastaA fastaB  outfile filetype"
    else:
        diff(*sys.argv[1:5])
