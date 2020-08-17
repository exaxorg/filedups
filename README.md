This project provides a fast and extendable way to find duplicate
image files in a file system.  With straightforward modifications it
works on any types of files.

<br><br>
<p align="center">
  <img width="2000" src="https://github.com/exaxorg/pubdata/blob/master/repo_pictures/pictures.svg">
</p>
<br><br>

Finding duplicates is based on computing hash digests of all files
recursively in the input path.  Computing hash digests is a relatively
expensive operation.  To minimise execution time, the script can use
all cores on the machine to run computations in parallel.

A key feature is that the script will re-use old computations as much
as possible:

  - The first time the script runs, it computes hash digests
    of all files in the file hierarchy.

  - When it is run again, previous results will be re-used, *unless*
    there are modifications in the input file hierarchy.  Only then it
    has to compute new hash digests.

Re-using computations does not only save time.  It can also be used to
*ensure* that the output result is *correct*, since running the script
will tell if it re-uses previous results or if it has to compute
something for the first time.

The approach is thus reproducible, transparent, and runs in parallel
on multi-core computers.

The project can be used as a skeleton to design more advanced file and
directory manipulations on an image set.



Performance
----

The script has been profiled on [this
machine](https://expertmakeraccelerator.org/performance/2019/09/02/bigdata_on_inexpensive_workstation.html).
The machine is inexpensive and far from state-of-the-art, but using
the Accelerator the performance is impressive.

The tested file system is composed of more than 116.000 files
separated into 1360 directories, occupying a total of 704GiB.
Scanning this file system takes 466 seconds.  Finding the actual
duplicates adds another two seconds to that.  Since the jobs are
parallelised by the Accelerator, computation speed is on average
**above 1.5GiB/second**.



Setup and Run the Example
-----

([TL;DR](https://en.wiktionary.org/wiki/tl;dr): `git clone`, `cd`, `pip install accelerator`, `ax server`, `ax run`.)

1. Clone this repository, `cd` into it.


1. Set up a virtual environment and install the Accelerator

   ```
   python3 -m venv venv
   source venv/bin/activate
   pip install accelerator
   ```

1. The Accelerator is a client-server application, so use two terminal
   emulator windows.  Make sure to activate the virtual environment in
   both of them!

   In the "server" terminal, type
   ```
   ax server
   ```

   In the "client" terminal, type
   ```
   ax run
   ```
   or
   ```
   ax run --fullpath
   ```

   The program will now execute.

   A report file presenting all duplicates will be generated in the
   `./results/` directory.

   There is also an alternative implementation, see separate section below,
   that is run by
   ```
   ax run alternative
   ```



1. (Optional) The output file can also be accessed from the
   Accelerator Board server.  Run

   ```
   ax board
   ```

   and point a web browser to `http://localhost:8520`.  All jobs, data,
   and code associated with the result file can be browsed this way.


The source code is found in the build script `dev/build.py`, which
calls the methods `dev/a_*.py` as well as some built in Accelerator
methods.



Customise the Setup
------

1. Point to your data.

   The path from where input images will be read is defined in the
   main build script, `dev/build.py`.  A set of valid file extensions
   to use are defined in the same file.


1. Modify the configuration file.

   The file `./accelerator.conf` defines paths and the number of
   parallel processes to use.  Modify this file to suit your system, it
   is well documented.



How it Works
----------

The build script is `dev/build.py`.  (Have a look, the script is
commented!)  This is how it works:

The first part computes hash digests for all files' contents,
basically like this

1. First, it calls the method `scan`, that will recursively scan all
   files and directories in the supplied path.  Files not matching the
   set of valid extensions as well as soft links are ignored.

1. The `scan` method will then launch subjobs, one subjob of type
   `scandir` *for each directory* containing at least one valid file.

1. The `scandir` method will compute a hash digest for each valid file
   in the assigned directory, and store it along with the file's name
   and size in a dataset.

1. When all subjobs have executed, the `scan` job will terminate,
   returning a list of all `scandir` jobs.

When the `scan` method completes execution, the returned data is a
list of jobs.  Each job contains one dataset containing data on all
files in one directory.

The next part reads all datasets and finds duplicates by looking at
the hash digests.

1. A job `dataset_list_to_chain` converts the list of jobs (with
   datasets) to a single dataset *chain*.

   Chains are the preferred way to work with multiple datasets.  The
   reason that the `scandir` jobs are not chained directly is to keep
   them completely independent of each other.  This is beneficial if
   there are modifications in the directory hierarchy, since only jobs
   affected by the modifications need to be computed.  Constructing a
   chain later is basically done by creating a set of links, which is
   of very low cost.

1. The dataset chain is then fed to the built-in `dataset_hashpart`
   method.  This method will partition the data based on the hash
   digest column so that each value can only appear in one slice.

   This means that finding duplicates can be carried out in parallel,
   independently in each slice.

1. The hash partitioned dataset is then sorted independently in each
   slice.  Sorting ensures that if there are several rows (files) with
   the same hash digest, they will appear on consecutive lines.

1. Finally, the method `duplicates` will read the sorted dataset, and
   compare the hash digests, line by line.  If there are duplicates,
   they will appear on adjacent lines.

   Since the dataset is hash partitioned and sorted, the `duplicates`
   method can run in parallel on all slices simultaneously.

   A report file will be linked to the result directory.



An Alternative Approach
-------

There is also a second build script, `build_alternative`, that does
the directory scanning directly in the build script, as well as
creating and storing Urd sessions of the jobs being executed.  This
separation makes it possible to run the duplicate finder part without
running the file scanning part, which is great when modifying or
extending the duplicate finding methods, since they can be executed
*without* re-running the possibly time consuming directory scanning
part.  Using Urd also allows for browsing all previous runs of the
script by timestamp, making it straightforward to track any changes in
the input and/or output over time.  Run the script like this

```
ax run alternative
```



New to the Accelerator?
------

The Accelerator is running *jobs* that are stored on disk for later
use.  Everything needed to run a job (input data references,
parameters, source code) as well as any generated output is recorded
in the job.  Jobs are built from *build scripts* or from other jobs
(then they are called *subjobs*).  Each job is associated with a
unique identifier called a *jobid*, such as for example `img-37`.

A job `build()`-call returns a Python "job object", containing
information about the job and links to its input and output.  If a job
has been built before, the job object is returned immediately and no
processing is done.  (Don't compute what already exists!)  Job objects
could be input to new job builds, allowing a job to make use of a
previous job's output data or results in a transparent way.

Any data created by a job is stored in the job's *job directory*.  All
results are stored with recipes describing how they were created.
Thus, knowing how a result was came to ("this code on this data with
these parameters"), means that the result can be fetched immediately
just by calling `build()`.  The wanted data is looked up using the
resulting job object.

A job can contain zero, one, or more *datasets*.  The dataset is an
efficient way of storing typed or untyped tabular data.  The data in a
dataset is *sliced* into a set of independent slices, to make parallel
access straightforward.  Datasets are named after the job that created
them, e.g. like this: `img-37/mydataset`.  The default, and typically
most common name is `default`, and in that case the name may be
omitted, so `img-37/default` is the same as `img-37`.  Thus, a jobid
`img-37` can also be used to reference its default dataset
`img-37/default`.

Two or more datasets can be *chained*, i.e. concatenated into one
dataset using links.  This way, datasets may grow in number of rows.
Similarly, new columns can be added to an existing dataset just by
linking columns from different datasets together.

The data in a dataset is available to a program through a Python
*iterator*.  The iterator can iterate over the data in a few different
ways, and the most common iteration is over a single slice of the
dataset.  A program is parallelised using a function called
`analysis()`.  The `analysis`-function takes a parameter `sliceno`,
which is a unique identifier for the current process.  This identifier
is fed to the iterator to get the right slice of the data out.  This
provides a straightforward way to write programs that operate on data
in parallel.

It is common to hash partition datasets based on the values in one of
its columns.  Hash partitioning ensures that all rows with a certain
value in the hashing column ends up in the same slice.  This reduces
the need for expensive merging operation typically otherwise
associated with parallel data processing.

The Accelerator comes with a set of "standard methods" for various
common tasks, among them a fast tabular file reader and a powerful
data parser and data typing method.  (Strict typing is important in
serious data science tasks.)

To get started, there are some command line tools to try after the
build script has been executed.  Try for example

 - `ax help` for an overview of commands, then `ax command --help` for
   help on individual commands.

 - `ax board` to start a web server for browsing jobs and datasets.
   Point a browser to `http://localhost:8520` to get started!

 - `ax method` to get a list and description of all available methods

 - `ax job <jobid>` to get information about a particular job.  It will
   show, among other things, all parameters as well as all files and
   datasets created by (and stored in) the job.

 - `ax dsinfo <jobid[/dataset]>` to learn about a dataset.  This
   command is powerful, please have a look at the help information
   using `--help`.

 - Using `ax run --fullpath` will print out the full path for each job
   directory.  The curious will use this for manual investigation of
   the job directories!


References
-------
The Accelerator's home page [exax.org](https://exax.org/).<br>
The Accelerator's github page [github.com/exaxorg](https://github.com/exaxorg).<br>
The Accelerator's [Reference Manual](https://berkeman.github.io/pdf/acc_manual.pdf).<br>

The Accelerator on [github.com/eBay](https://github.com/ebay/accelerator).<br>
The Accelerator on [eBay's Tech Blog](https://tech.ebayinc.com/engineering/announcing-the-accelerator-processing-1-000-000-000-lines-per-second-on-a-single-computer).<br>
The Accelerator on [Hacker News](https://news.ycombinator.com/item?id=16999441).<br>
The Accelerator on [PyPI](https://pypi.org/project/accelerator/).<br>



License
-------

Copyright 2020 Anders Berkeman, Carl Drougge, and Sofia Hörberg.

Licensed under the Apache License, Version 2.0 (the "License"); you
may not use this file except in compliance with the License. You may
obtain a copy of the License at

```
https://www.apache.org/licenses/LICENSE-2.0
```

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied. See the License for the specific language governing
permissions and limitations under the License.
