from classes.ChewbaccaProgram import ChewbaccaProgram
from classes.Helpers import getInputFiles, debugPrintInputInfo, init_pool, run_parallel, printVerbose, strip_ixes, \
    cleanup_pool, bulk_move_to_dir, makeAuxDir, validate_paired_fastq_reads, move
from classes.ProgramRunner import ProgramRunner, ProgramRunnerCommands


class Preclean_Program_Bayeshammer(ChewbaccaProgram):
    """Uses bayeshammer (Spades) to fix sequencing errors via kmer clustering and probabilistic substitution.
    """
    name = "bayeshammer"

    def execute_program(self):
        args = self.args
        self.preclean_bayeshammer(args.input_f, args.input_r, args.outdir, args.processes, args.bayesthreads,
                                  args.extraargstring)

    def preclean_bayeshammer(self, input_f, input_r, outdir, processes, bayesthreads, extraargstring):
        """Assembles reads from two (left and right) fastq files/directories.

        :param input_f: File path to file or folder of left reads to clean.
        :param input_r: File path to file or folder of right reads to clean.
        :param outdir: Filepath to output directory.
        :param bayesthreads: The number of threads per process to use.
        :param processes: The maximum number of processes to use.
        :param kmerlen: The kmer length to use.  Default: 16.
        :param extraargstring: Advanced program parameter string.
        """
        # Collect input files, and validate that they match
        inputs = validate_paired_fastq_reads(input_f, input_r)
        pool = init_pool(min(len(inputs), processes))
        printVerbose("\tPrecleaning %s reads with Spades-Baye's Hammer..." % len(inputs))
        debugPrintInputInfo(inputs, "preclean/fix.")

        run_parallel([ProgramRunner(ProgramRunnerCommands.PRECLEAN_SPADES,
                                    [forwards, reverse, outdir, bayesthreads],
                                    {"exists": [forwards, reverse], "positive": [bayesthreads]},
                                    extraargstring)
                      for forwards, reverse in inputs], pool)
        printVerbose("Done cleaning reads.")

        # Grab all the auxillary files (everything not containing ".assembled."
        # aux_files = getInputFiles(outdir, "*", "*.assembled.*", ignore_empty_files=False)
        # make aux dir for extraneous files and move them there
        # bulk_move_to_dir(aux_files, makeAuxDir(outdir))

        # Select output files
        aux_files = getInputFiles(outdir, "*", ignore_empty_files=False)
        corrected_dir = "%s/corrected" % outdir
        bulk_move_to_dir(getInputFiles(corrected_dir, "*"), outdir)
        aux_files += getInputFiles(outdir, "*unpaired*", ignore_empty_files=False)
        aux_files += getInputFiles(outdir, "configs", ignore_empty_files=False)

        # Gather aux files
        aux_dir = makeAuxDir(outdir)
        bulk_move_to_dir(aux_files, aux_dir)

        # Rename output files
        output_files = getInputFiles(outdir, "*", "corrected_*")
        for out_file in output_files:
            move(out_file, "%s/%s_corrected.fastq" % (outdir, strip_ixes(out_file)))

        # move the last minute log file
        try:
            move("%s/corrected_corrected.fastq" % outdir, "%s/corrected_corrected.fastq" % aux_dir)
        except:
            pass
        cleanup_pool(pool)
