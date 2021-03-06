'''
remove primers from a fastq
'''

from Bio import SeqRecord, SeqIO, Seq

class TrimmedRecords:
    '''class for iterating through fastq and trimming'''

    def __init__(self, primer, fastq_records, window, max_diffs):
        self.primer = primer
        self.fastq_records = fastq_records
        self.window = window
        self.max_diffs = max_diffs

        self.matching_chars = {('A', 'A'): 1, ('C', 'C'): 1, ('T', 'T'): 1, ('G', 'G'): 1, ('W', 'A'): 1, ('W', 'T'): 1, ('S', 'C'): 1, ('S', 'G'): 1, ('M', 'A'): 1, ('M', 'C'): 1, ('K', 'G'): 1, ('K', 'T'): 1, ('R', 'A'): 1, ('R', 'G'): 1, ('Y', 'C'): 1, ('Y', 'T'): 1, ('B', 'C'): 1, ('B', 'G'): 1, ('B', 'T'): 1, ('D', 'A'): 1, ('D', 'G'): 1, ('D', 'T'): 1, ('H', 'A'): 1, ('H', 'C'): 1, ('H', 'T'): 1, ('V', 'A'): 1, ('V', 'C'): 1, ('V', 'G'): 1, ('N', 'A'): 1, ('N', 'C'): 1, ('N', 'G'): 1, ('N', 'T'): 1}

    def __iter__(self):
        return self

    def __next__(self):
        best_diffs = None
        while best_diffs is None or best_diffs > self.max_diffs:
            record = next(self.fastq_records)
            seq = str(record.seq)
            pl = len(self.primer)

            best_i = None
            best_score = None

            for i in range(self.window):
                # if the sequence is short, then the primer in this window might not
                # even fit in the sequence
                if len(seq) <= i + pl:
                    continue

                diffs = self.hamming(seq[i: i + pl])
                if diffs == 0:
                    return record[i + pl:]
                else:
                    if best_diffs is None or diffs < best_diffs:
                        best_diffs = diffs
                        best_i = i

        return record[best_i + pl:]

    def hamming(self, seq):
        if len(seq) != len(self.primer):
            raise RuntimeError("Hamming distance must be between equal length sequences, got sequence with length {} and primer with length {}".format(len(seq), len(self.primer)))

        dist = 0
        for pair in zip(self.primer, seq):
            if pair not in self.matching_chars:
                dist += 1

        return dist


class SecondTrimmedRecords(TrimmedRecords):
    '''
    class for iterating through fastq and trimming second primer
    
    Unlike the first one, it does NOT throw away an entry without a matching bit
    '''

    # swo> todo: - use operator.ne for hamming
    #            - make pl an instance variable

    def __next__(self):
        best_diffs = None
        record = next(self.fastq_records)
        seq = str(record.seq)
        pl = len(self.primer)

        best_i = None
        best_score = None

        for i in range(self.window):
            # count the number of differences. need a funny 'else' here because
            # python takes s[-0] as s[0], i.e., the first character
            if i == 0:
                diffs = self.hamming(seq[-pl: ])
            else:
                diffs = self.hamming(seq[-(pl + i): -i])

            if diffs == 0:
                return record[0: -(pl + i)]
            else:
                if best_diffs is None or diffs < best_diffs:
                    best_diffs = diffs
                    best_i = i

        # if the differences were good, return the trimmed version. otherwise,
        # return the whole thing, unchanged
        if best_diffs < self.max_diffs:
            return record[0: -(pl + best_i)]
        else:
            return record


class PrimerRemover:
    def __init__(self, primer, fastq, window, max_diffs, output):
        fastq_entries = SeqIO.parse(fastq, 'fastq')
        entries = TrimmedRecords(primer, fastq_entries, window, max_diffs)
        for entry in entries:
            SeqIO.write(entry, output, 'fastq')

class SecondPrimerRemover:
    def __init__(self, primer, fastq, window, max_diffs, output):
        fastq_entries = SeqIO.parse(fastq, 'fastq')
        entries = SecondTrimmedRecords(primer, fastq_entries, window, max_diffs)
        for entry in entries:
            SeqIO.write(entry, output, 'fastq')
