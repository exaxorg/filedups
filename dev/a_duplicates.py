from collections import defaultdict

datasets = ('source',)


description = '''
Find duplicate entries in source dataset.

Duplicates are found based on (hash digest + file size).  The dataset
has to be hash partitioned and sorted on the hash digest column.  (The
method also verifies this.)
'''


def analysis(sliceno):
	# Check for duplicates is easy since the dataset is sorted on the file hash column.
	duplicates = defaultdict(set)
	prev = ('', None, None)
	for curr in datasets.source.iterate(sliceno, ('filehash', 'filesize', 'filename'), hashlabel='filehash'):
		assert curr[0] >= prev[0], 'dataset must be sorted'
		if curr[:2] == prev[:2]:
			hash = ':'.join(str(x) for x in curr[:2])
			duplicates[hash].add(prev[2])
			duplicates[hash].add(curr[2])
		prev = curr
	return duplicates

def synthesis(analysis_res, job):
	duplicates = analysis_res.merge_auto()

	with job.open('duplicates.txt', 'wt') as fh:
		fh.write('Num duplicates: %d\n' % (len(duplicates),))
		for ix, (key, val) in enumerate(sorted(duplicates.items())):
			fh.write('%6d %s %s\n' % (ix, key, ' '.join(sorted(val))))
