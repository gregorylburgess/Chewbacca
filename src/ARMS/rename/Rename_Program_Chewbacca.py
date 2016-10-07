import os
from classes.ChewbaccaProgram import *
from classes.ProgramRunner import *
from classes.Helpers import *
from Bio import SeqIO

class Rename_Program_Chewbacca(ChewbaccaProgram):
    name = "chewbacca"

    def execute_program(self):
        args = self.args
        self.rename_chewbacca(args.input_f, args.outdir, args.filetype, args.clip, args.processes)

    def rename_chewbacca(self, input_f, outdir, filetype, clip, processes):
        """Renames sequences in a fasta/fastq file as <filename>_ID0, <filename>_ID1, <filename>_ID2, etc., where
            <filename> is the name of the fasta/fastq file without any extensions or chewbacca suffixes.

        :param input_f: Filepath to an input file or folder to rename.
        :param outdir: Filepath to the output directory.
        :param filetype: Either 'fasta' or 'fastq'.
        :param clip: If True, remove dereplication counts from sequence names before renaming.
        :param processes: The maximum number of processes to use.
        """

        # Gather input files
        inputs = getInputFiles(input_f)
        debugPrintInputInfo(inputs, "rename")
        pool = init_pool(min(len(inputs), processes))
        printVerbose("Renaming sequences...")
        # Run serialRename in parallel
        parallel(runPythonInstance,
                 [(serialRename,
                   input_, "%s/%s_renamed%s" % (outdir, strip_ixes(input_), os.path.splitext(input_)[1]),
                   filetype, clip) for input_ in inputs], pool)
        printVerbose("Done renaming sequences...")

        samples_dir = makeDirOrdie("%s_samples" % outdir)
        samples_files = getInputFiles(outdir, "*.samples", ignore_empty_files=False)
        bulk_move_to_dir(samples_files, samples_dir)

        aux_dir = makeAuxDir(outdir)
        aux_files = getInputFiles(outdir, "*.mapping", ignore_empty_files=False)
        bulk_move_to_dir(aux_files, aux_dir)

        cleanup_pool(pool)


def serialRename(input_file, output_fasta_filepath, file_type, clip=True):
    """Takes in a fasta file and outputs a new fasta with the sequences renamed.  Renaming convention is x.y.z<n> for
        x.y.z.fasta, where n is an integer in the range [0:n] where n is the position of the sequence in the input_file.
        Also writes a groups file, linking each sequence to its parent sample.
        e.g. The sequences in SiteX_SampleA.fasta are renamed:
                SiteX_SampleA_0, SiteX_SampleA_1, SiteX_SampleA_2, etc.
    :param input_file:      Input fasta or fastq file.
    :param output_fasta_filepath:     Filepath for the output .samples file.
    :param file_type:       "fasta" or "fastq"
    """

    samples_file = "%s/%s_renamed.samples" % (os.path.dirname(output_fasta_filepath), strip_ixes(input_file))
    name_map_file = "%s/%s_renamed.mapping" % (os.path.dirname(output_fasta_filepath), strip_ixes(input_file))
    seqPrefix = strip_ixes(input_file)
    i = 0

    with open(output_fasta_filepath, 'w') as output:
        with open(name_map_file, 'w') as mapping_file_output:
            with open(samples_file, 'w') as samples_file_output:

                samples_map = []
                name_map = []
                renamed_seqs = []

                for s in SeqIO.parse(input_file, file_type):
                    i += 1
                    # Buffered write
                    if i % 5000 == 0:
                        mapping_file_output.write("".join(name_map))
                        name_map = []
                        samples_file_output.write("".join(samples_map))
                        samples_map = []
                        SeqIO.write(renamed_seqs, output, file_type)
                        renamed_seqs = []

                    # Store the old_name new_name mapping
                    old_id = s.id
                    s.id = "%s_ID%s" % (seqPrefix, i)
                    name_map.append("%s\t%s\n" % (old_id, s.id))

                    # Store the sequence-sample map
                    samples_map.append("%s\t%s\n" % (s.id, clip_count(seqPrefix, '_')))

                    # Store the renamed sequence
                    s.description = ""
                    renamed_seqs.append(s)

                mapping_file_output.write("".join(name_map))
                samples_file_output.write("".join(samples_map))
                SeqIO.write(renamed_seqs, output, file_type)