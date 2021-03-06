from classes.ChewbaccaProgram import ChewbaccaProgram
from classes.ProgramRunner import ProgramRunner, ProgramRunnerCommands
from classes.Helpers import getInputFiles, init_pool, debugPrintInputInfo, printVerbose, run_parallel, strip_ixes, \
                                bulk_move_to_dir, cleanup_pool, makeAuxDir


class Clean_Adapters_Program_Flexbar(ChewbaccaProgram):
    """Uses flexbar to trim adapters (and preceeding barcodes) from sequences in input file(s).  Sequences should be in
        the following format: <BARCODE><ADAPTER><SEQUENCE><RC_ADAPTER>, where ADAPTER is defined in the adapters file,
        and RC_ADAPTER is defined in the rcadapters file."""
    name = "flexbar"


    def execute_program(self):
        args = self.args
        self.clean_trim_adapters_flexbar(args.input_f, args.adapters, args.adaptersrc, args.outdir, args.allowedns,
                                         args.processes, args.extraargstring)


    def clean_trim_adapters_flexbar(self, input_f, adapters, adaptersrc, outdir, allowedns, processes, extraargstring):
        """Use flexbar to trim adapters and barcodes from sequences.  By default, Flexbar does not allow any 'N' \
            characters in SEQUENCE, and will toss any sequences that do contain 'N'.  To avoid this, use the -u or \
            --allowedns flags to specify the maximum number of 'N's to allow

        :param input_f: Filepath to input file or folder.
        :param adapters: Filepath to a list of adapters.
        :param adaptersrc: Filepath to a list of reverse-complemented adapters.
        :param outdir: Filepath to the output directory.
        :param allowedns: Non-negative integer value indicating the maximum number of 'N's to tolerate in a sequence.
        :param processes: The maximum number of processes to use.
        :param extraargstring: Advanced program parameter string.
        """
        inputs = getInputFiles(input_f)
        pool = init_pool(min(len(inputs), processes))
        debugPrintInputInfo(inputs, "trim adapters from")
        # "flexbar":  "flexbar -r \"%s\" -t \"%s\" -ae \"%s\" -a \"%s\"",
        printVerbose("Trimming barcodes and adapters with flexbar")
        temp_file_name_template = "%s/temp_%s"
        debarcoded_file_name_template = "%s/%s_debarcoded"
        # Trim adapters from the left
        run_parallel([ProgramRunner(ProgramRunnerCommands.TRIM_FLEXBAR,
                                    [input_file, temp_file_name_template % (outdir, strip_ixes(input_file)),
                                     "LEFT", adapters, allowedns],
                                    {"exists": [input_file, adapters]}, extraargstring)
                      for input_file in inputs], pool)

        temp_files = getInputFiles(outdir, "temp_*")
        debugPrintInputInfo(temp_files, "trim adapters from")

        # Trim the reverse complemented adapters from the right
        run_parallel([ProgramRunner(ProgramRunnerCommands.TRIM_FLEXBAR,
                                    [input_file, debarcoded_file_name_template % (outdir, strip_ixes(input_file)[5:]),
                                     "RIGHT", adaptersrc, allowedns],
                                    {"exists": [input_file, adaptersrc]}, extraargstring)
                      for input_file in temp_files], pool)
        printVerbose("Done Trimming sequences.")

        # Move temp files
        aux_files = getInputFiles(outdir, "temp_*", ignore_empty_files=False)
        bulk_move_to_dir(aux_files, makeAuxDir(outdir))
        cleanup_pool(pool)
