datasets = (['source'],)


description='''
Convert a dataset list into a dataset chain.
'''


def synthesis(job):
	assert len(datasets.source) >= 1, 'Needs at least one dataset!'
	source = datasets.source
	last = source.pop(-1)
	previous = None
	for ix, ds in enumerate(source):
		previous = ds.link_to_here(override_previous=previous, name=str(ix))
	last.link_to_here(override_previous=previous, name='default')
