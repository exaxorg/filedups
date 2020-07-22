import os
import hashlib


options = dict(
	directory=str,
	files=[],
)


description = '''
Create a dataset of hash digests and file meta info.

The dataset contains
  - file name,
  - file size, and
  - hash digest of file's contents
for all files in options.files residing in options.directory.
'''


def prepare(job):
	dw = job.datasetwriter()
	dw.add('filename', 'unicode')
	dw.add('filehash', 'unicode')
	dw.add('filesize', 'int64')
	return dw


def analysis(sliceno, slices, prepare_res):
	dw = prepare_res
	for fn in options.files[sliceno::slices]:
		fn = os.path.join(options.directory, fn)
		with open(fn, 'rb') as fh:
			data = fh.read()
			dw.write(fn, hashlib.md5(data).hexdigest(), len(data))
