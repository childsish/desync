from desync import desync


def check_read_quality(read_file):
    print(f'checking read quality for {read_file}')
    return read_file + '.txt'


def trim_reads(read_file, mate_read_file):
    print(f'trimming {read_file} and {mate_read_file}')
    return 'trimmed_' + read_file, 'trimmed_' + mate_read_file


def align_reads(read_file, mate_read_file, genome_file):
    print(f'aligning {read_file} and {mate_read_file} with {genome_file}')
    start = 0
    while start < len(read_file):
        if read_file[start] != mate_read_file[start]:
            break
        start += 1
    return read_file[:start] + '.bam'


def quantify_transcripts(aligned_read_files, transcripts_file):
    print(f'quantifying transcripts in {transcripts_file} using reads from {aligned_read_files}')
    return transcripts_file + '.txt'


def analyse_differential_expression(transcript_quantities_file, sample_description, experiemental_design):
    print(f'analysing differential expression using transcripts from {transcript_quantities_file}, samples described in {sample_description} and the experimental design from {experiemental_design}')
    return transcript_quantities_file + '.txt'


@desync
def align_reads_workflow(read_file, mate_read_file, genome_file):
    check_read_quality(read_file)
    check_read_quality(mate_read_file)
    trimmed_read_file, trimmed_mate_read_file = trim_reads(read_file, mate_read_file)
    check_read_quality(trimmed_read_file)
    check_read_quality(trimmed_mate_read_file)
    return align_reads(trimmed_read_file, trimmed_mate_read_file, genome_file)


@desync
def differential_expression_workflow(
    read_files,
    mate_read_files,
    genome_file,
    transcripts_file,
    sample_decription,
    experimental_design,
):
    aligned_read_files = [align_reads_workflow(read_file, mate_read_file, genome_file) for read_file, mate_read_file in zip(read_files, mate_read_files)]
    transcript_quantities = quantify_transcripts(aligned_read_files, transcripts_file)
    return analyse_differential_expression(transcript_quantities, sample_decription, experimental_design)


if __name__ == '__main__':
    res = differential_expression_workflow(
        ['A_01.fasta.gz', 'B_01.fasta.gz', 'C_01.fasta.gz', 'D_01.fasta.gz', 'E_01.fasta.gz'],
        ['A_02.fasta.gz', 'B_02.fasta.gz', 'C_02.fasta.gz', 'D_02.fasta.gz', 'E_02.fasta.gz'],
        'genome.fasta.gz',
        'transcripts.gtf.gz',
        'sample_description.txt',
        'experimental_design.txt',
    )
    print(res)
