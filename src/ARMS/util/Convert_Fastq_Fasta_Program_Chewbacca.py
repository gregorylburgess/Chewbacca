from classes.ChewbaccaProgram import *
from classes.ProgramRunner import *
from util.fastqToFasta import translateFastqToFasta

from classes.Helpers import *


class Convert_Fastq_Fasta_Program_Chewbacca(ChewbaccaProgram):
    name = "chewbacca"

    def execute_program(self):
        args = self.args
        self.convert_chewbacca(args.input_f, args.outdir, args.threads)

    def convert_chewbacca(self, input_f, outdir, threads):
        makeDirOrdie(outdir)
        inputs = getInputFiles(input_f)
        debugPrintInputInfo(inputs, "convert to fasta.")
        printVerbose("Converting to fasta...")
        pool = init_pool(min(len(inputs), threads))
        parallel(runPythonInstance, [(translateFastqToFasta, input_, "%s/%s.fasta" % (outdir, getFileName(input_)))
                                     for input_ in inputs], pool)
        printVerbose("Done converting.")
        cleanup_pool(pool)