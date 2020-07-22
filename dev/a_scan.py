from os import walk
from os.path import splitext, islink, join

from accelerator.subjobs import build


options = dict(path=str, validextensions={str}, dummy=None)


description = '''
Wrapper around the "scan" method.

Iterate over all subdirectories in options.path and build a subjob
"scan" for each one.  Return a list of all subjobs.

This method could be run "unconditionally" by feeding for example the
current time stamp to options.dummy.
'''


def synthesis(job):
	ix = 0
	jobs = []
	for current, subdirs, files in walk(options.path):
		files = sorted(x for x in files if splitext(x)[1].upper() in options.validextensions and not islink(join(current, x)))
		if files:
			jobs.append(build('scandir', directory=current, files=sorted(files)))
			print(ix, current)
			ix += 1
	return jobs
