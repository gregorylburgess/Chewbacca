from classes.ChewbaccaProgram import ChewbaccaProgram
from classes.Helpers import getInputFiles, debugPrintInputInfo, init_pool, run_parallel, printVerbose, strip_ixes, \
    cleanup_pool, bulk_move_to_dir, makeAuxDir
from itertools import product
from classes.PythonRunner import PythonRunner
from queryVSearchoutForTaxa import parseVSearchOutputAgainstNCBI
from Query_Helpers import query_vsearch


class Query_OTU_DB_Program_Vsearch(ChewbaccaProgram):
    name = "vsearch"

    def execute_program(self):
        args = self.args
        self.query_fasta_db_vsearch(args.input_f, args.outdir, args.referencefasta, args.db, args.simmilarity,
                                    args.coverage, args.processes, args.extraargstring)

    def query_fasta_db_vsearch(self, input_f, outdir, ref_fasta, ref_db, simmilarity, coverage, processes,
                               extraargstring):
        """Compare reference sequences to the fasta-formatted query sequences, using global pairwise alignment.

        :param input_f:  Filepath to a file or folder of files to identify.
        :param outdir: Filepath to the output directory.
        :param ref_fasta: Filepath to the curated fasta file to use as a reference.
        :param ref_db: Filepath to the curated fasta file to use as a reference.
        :param simmilarity:"Minimum % simmilarity (decimal between 0 and 1) between query and reference sequences
                            required for positive identification.
        :param coverage:Minimum % coverage (decimal between 0 and 1) required query and reference sequences required
                            for positive identification.
        :param processes: The number of processes to use in the identification process.
        :param extraargstring: Advanced program parameter string.
        """
        # blast6 output format http://www.drive5.com/usearch/manual/blast6out.html
        aln_user_string = "--userfields query+target+id+alnlen+qcov"
        # coi_fasta = os.path.expanduser("~/ARMS/refs/COI.fasta")
        # ncbi_db_string = os.path.expanduser("~/ARMS/refs/ncbi.db")
        coi_fasta = ref_fasta
        ncbi_db_string = ref_db

        query_fastas = getInputFiles(input_f)
        debugPrintInputInfo(query_fastas, "queried against the DB.")
        inputs = [x for x in product(query_fastas, [coi_fasta])]
        pool = init_pool(min(len(query_fastas), processes))

        # VSEARCH ALIGNMENT
        query_vsearch(inputs, outdir, simmilarity, processes, aln_user_string, extraargstring, pool)

        printVerbose("Parsing output...")
        # Parse the alignment results and put those that pass the criterion (97 similarity, 85 coverage) in
        # parsed_BIOCODE.out.  Parameters can be changed and this command can be rerun as many times as necessary
        #
        # parseVSearchOutputAgainstNCBI(vsearch_out, ncbi_db, min_coverage, min_similarity)> parsed_nt.out
        run_parallel([PythonRunner(parseVSearchOutputAgainstNCBI,
                                   ["%s/%s.out" % (outdir, strip_ixes(query)), ncbi_db_string,
                                    "%s/%s.tax" % (outdir, strip_ixes(query)), simmilarity, coverage],
                                   {"exits": [query, ncbi_db_string]})
                      for query in query_fastas], pool)
        printVerbose("Done processing.")

        # Gather and move auxillary files
        aux_files = getInputFiles(outdir, "*", "*.tax", ignore_empty_files=False)
        bulk_move_to_dir(aux_files, makeAuxDir(outdir))

        cleanup_pool(pool)
