from os import walk
from os.path import splitext, islink, join
from datetime import datetime


def main(urd):

	# Change to "path = <mypath>, or modify input_directory in
	# accelerator.conf".  Add/remove extensions as appropriate.
	# Use do_scan boolean to turn on/off scanning.
	path = urd.info.input_directory
	validextensions = {'.JPG', '.NEF', '.PNG', '.GIF', '.TIFF', '.BMP'}
	do_scan = True

	def scan(path, verbose=True):
		# Scan all directories recursively and run "scandir" jobs for
		# those directories that contain files matching the
		# "validextensions" set.  Return a list of all jobs.
		ix = 0
		jobs = []
		for current, subdirs, files in walk(path):
			files = sorted(x for x in files if splitext(x)[1].upper() in validextensions and not islink(join(current, x)))
			if files:
				jobs.append(urd.build('scandir', directory=current, files=files))
				if verbose:
					print(ix, current)
				ix += 1
		return jobs

	# scan the path
	if do_scan:
		ts = datetime.now()
		urd.begin('scan', ts)
		jobs = scan(path)
		job = urd.build('dataset_list_to_chain', source=jobs)
		urd.finish('scan')

	# fetch result from scanning, find duplicates
	urd.begin('proc')
	scan = urd.latest('scan')
	ts = scan.timestamp
	job = scan.joblist['dataset_list_to_chain']
	job = urd.build('dataset_hashpart', source=job, hashlabel='filehash')
	job = urd.build('dataset_sort', source=job, sort_columns=('filehash', 'filename',))
	dup = urd.build('duplicates', source=job)
	dup.link_result('duplicates.txt')
	urd.finish('proc', ts)
