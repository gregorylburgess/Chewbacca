from classes.ChewbaccaProgram import ChewbaccaProgram
from classes.Helpers import getInputFiles, debugPrintInputInfo, init_pool, run_parallel, printVerbose, strip_ixes, \
    makeAuxDir, bulk_move_to_dir, cleanup_pool, makeDirOrdie
from classes.ProgramRunner import ProgramRunner, ProgramRunnerCommands
from classes.PythonRunner import PythonRunner
from parse.parseUCtoGroups import parseUCtoGroups
from rename.renameWithoutCount import removeCountsFromGroupsFile
from Cluster_Helpers import handle_groups_file_update


class Cluster_Program_Vsearch(ChewbaccaProgram):
    name = "vsearch"

    def execute_program(self):
        args = self.args
        self.cluster_vsearch(args.input_f, args.outdir, args.groupsfile, args.processes, args.idpct,
                             args.extraargstring)

    def cluster_vsearch(self, input_f, outdir, groupsfile, processes, idpct, extraargstring):
        """Clusters sequences using SWARM.
        :param input_f: A file or folder containing fasta files to cluster.
        :param outdir: The output directory results will be written to.
        :param groupsfile: A groups file or folder containinggroups files that describe the input. Note: if no groups
                            file is supplied, then entries in the fasta file are assumed to be singleton sequences.
        :param idpct: Real number in the range (0,1] that specifies the minimum simmilarity threshold for
                            clustering.  e.g. .95 indicates that a candidate sequence 95% must be at least
                            95% simmilar to the seed sequence to be included in the cluster.
        :param processes: The maximum number of processes to use.
        :param extraargstring: Advanced program parameter string.
        """
        # Grab the fasta file(s) to cluster
        inputs = getInputFiles(input_f)
        debugPrintInputInfo(inputs, "clustered")
        pool = init_pool(min(len(inputs), processes))

        # RUN CLUSTERING
        # " --cluster_size %s -id %f --centroids %s  --uc %s",
        run_parallel([ProgramRunner(ProgramRunnerCommands.CLUSTER_VSEARCH,
                                    [input_, float(idpct), "%s/%s_seeds.fasta" % (outdir, strip_ixes(input_)),
                                     "%s/%s_clustered_uc" % (outdir, strip_ixes(input_))],
                                    {"exists": [input_]}, extraargstring) for input_ in inputs], pool)

        # PARSE UC FILE TO GROUPS FILE
        printVerbose("Parsing the clustered uc files to groups files")
        clustered_uc_files = getInputFiles(outdir, "*_clustered_uc")
        debugPrintInputInfo(clustered_uc_files, "parsed to groups")
        run_parallel([PythonRunner(parseUCtoGroups, [input_, "%s/%s.groups" % (outdir, strip_ixes(input_))],
                                   {"exists": [input_]})
                      for input_ in clustered_uc_files], pool)

        # REMOVE COUNTS FROM CLUSTERING GROUPS FILE
        printVerbose("Cleaning the .groups file from clustering")
        # Grab the current groups file and the new clustered groups file (which needs to be cleaned)
        clustered_groups_files = getInputFiles(outdir, "*_clustered.groups")
        # Remove counts from the clustering groups files
        debugPrintInputInfo(clustered_groups_files, "cleaned")
        run_parallel([PythonRunner(removeCountsFromGroupsFile,
                                   [input_, "%s/%s_uncount.groups" % (outdir, strip_ixes(input_))],
                                   {"exists": [input_]})
                      for input_ in clustered_groups_files], pool)
        printVerbose("Done cleaning groups files.")

        # Collect the groups file from clustering with counts removed
        cleaned_clustered_groups_files = getInputFiles(outdir, "*_uncount.groups", ignore_empty_files=False)

        # Resolve the user specified names file if necessary
        final_groups_files = handle_groups_file_update(outdir, groupsfile, cleaned_clustered_groups_files)

        # Move the final groups file(s) to the groups dir
        groups_dir = makeDirOrdie("%s_groups_files" % outdir)
        bulk_move_to_dir(final_groups_files, groups_dir)

        # Move aux files to the aux dir
        aux_files = getInputFiles(outdir, "*", "*_seeds.fasta", ignore_empty_files=False)
        aux_dir = makeAuxDir(outdir)
        bulk_move_to_dir(aux_files, aux_dir)

        # Cleanup the pool
        cleanup_pool(pool)
