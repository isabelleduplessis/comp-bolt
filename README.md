# Comp-BOLT

**Comp**utational **B**iology project **O**rganization, **L**ogging, and **T**racking.

v0.1.0

I created the command line tool `bolt` to make it easier to document thought processes while doing exploratory comp bio analyses, so that your code, reasoning, and review of results are all in the same place. This is intended to help organize quick and dirty analyses rather than well documented end to end pipelines.

`bolt` can essentially be used instead of `mkdir` and `touch` when starting exploratory analyses. When using `bolt` commands to create project directories, analysis directories, or job scripts, the user is prompted to enter a quick description of what the directory or file is for. These descriptions are saved in hidden files. 
- Every project and experiment directory gets a hidden `.bolt.yml` file
  storing its name, description, creation time, notes, update history, and
  (for experiments) its jobs.

Users can also use `bolt note` to type a note at any time, which will be saved to that directory's hidden metadata. This allows users to type their thoughts, reflections, and ideas right into the command line to be saved along with their code. 

The user can then get logs of their notes for a directory or whole projct. 



## Installation

```bash
pip install git+https://github.com/isabelleduplessis/comp-bolt.git
```

or, from a local clone:

```bash
git clone https://github.com/isabelleduplessis/comp-bolt.git
cd comp-bolt
pip install .
```

This installs the `bolt` command on your `PATH`.

## Easy Getting Started

For simplest use starting out, just use `bolt init`, `bolt new`, and `bolt log`.


### `bolt init`

Create a new project directory.

```bash
bolt init "ID002_spneumoniae_phylogeny"
bolt init "ID002_spneumoniae_phylogeny" -d "Placing a low coverage S. pneumoniae genome in a phylogeny"
```

If `-d`/`--description` is omitted, you'll be prompted for a description.

### `bolt new`

Create a new experiment directory inside the current directory. Must be run inside an existing project or experiment.

```bash
bolt new "pathphynder"
bolt new "pathphynder" -d "Testing PathPhynder placement using different reference genomes"
```

### `bolt log`

Generate a documentation report from `.bolt.yml` metadata. Prints to stdout. Archived items are excluded.

```bash
bolt log                    # full report for the current directory, in Markdown
bolt log > report.md
bolt log pathphynder        # scoped report for one experiment, printed to console
bolt log --plain       # plain text instead of Markdown
```

Example output:
```
# Project: bolt-test

## Description

testing out my new software!

**Created:** 2026-07-27

---

# Experiments

## mapping_bt2

### Description

mapping with bowtie2 rna reads

### Notes

- 2026-07-27: this is so cool that i can just record my thoughts
```

## More Options



### `bolt job`

Create a new job (script) inside the current experiment. Must be run inside an experiment (not a project root).

```bash
bolt job "run_pathphynder.sh"
bolt job "run_pathphynder.sh" -d "Pathphynder workflow with only GPSC1 genomes"

# Start from a copy of an existing script:
bolt job "run_pathphynder_v2.sh" -c run_pathphynder.sh -d "Pathphynder workflow GPSC1 genomes, change pileup read mismatch threshold to 1"
# Then manually change parameter
```

New jobs default to `pending` status, which can be reviewed by the user to take note of interpretation of the result.

### `bolt review`

Review a job and record its status. Searches the current directory and subdirectories.

```bash
bolt review                       # lists every pending job, e.g.:
                                   #   [1] ./job1.sh
                                   #   [2] ./exp2/job2.sh
bolt review run_pathphynder.sh    # review a specific job by name
bolt review ./exp2/job2.sh        # or by relative path, if names collide
```

The user is prompted for a status (`[s]uccess`, `[f]ail`, `[p]ending`,
`[i]nconclusive`) and a short status description. Jobs can be reviewed
multiple times; the full history is kept, and the most recent review is
what's shown as the job's current status.

**Pending job warning:** any `bolt` command run inside a project prints a
non-blocking warning like `3 jobs currently have pending status. Run bolt
review to update them.` if pending jobs exist anywhere in the project.

### `bolt note`

Add a timestamped note to the current project or experiment. (Jobs don't
have notes.)

```bash
bolt note "Received additional sequencing data."
bolt note                 # prompts you to type the note
bolt note -e / --edit     # fix a typo in an existing note (no history kept)
bolt note -v / --view     # print the notes for the current directory
```

### `bolt update`

Rename or re-describe a project, experiment, or job. Renaming also renames
the directory (or job file) on disk. Previous values are kept, with
timestamps, in an `updates` (or, for jobs, `update_history`) list.

```bash
bolt update pathphynder
```

You'll be prompted for a new name and/or new description; leave either
blank to keep it unchanged.

### `bolt archive`

Archive (or unarchive) a project, experiment, or job. Archived items stay in
metadata and remain recoverable, but are excluded from `bolt log` reports
and from `bolt review`'s job lists.

```bash
bolt archive pathphynder
bolt archive run_pathphynder.sh
bolt archive pathphynder -u / --unarchive
bolt archive -s / --status        # show active vs. archived items
```


## Metadata format

Each project/experiment directory has a hidden `.bolt.yml`. Examples:

**Project:**

```yaml
type: project
name: ID002_spneumoniae_phylogeny
description: >
  Placing a low coverage S. pneumoniae genome in a phylogeny.
created: 2026-07-01T09:00:00
notes:
  - timestamp: 2026-07-02T14:00:00
    text: Initial project setup complete.
updates: []
```

**Experiment:**

```yaml
type: experiment
name: pathphynder
description: >
  Testing PathPhynder placement using different reference genomes.
created: 2026-07-09T12:00:00
notes:
  - timestamp: 2026-07-10T09:15:00
    text: Have tried a few different input bam sets and none but have no derived SNPs with any of them.
updates: []
jobs:
  - name: run_pathphynder.sh
    description: >
      Pathphynder workflow with only GPSC1 genomes.
    created: 2026-07-09T12:30:00
    status: fail
    status_description: No derived SNPs error.
    review_timestamp: 2026-07-09T16:00:00
    update_history: []
```

## Development

```bash
pip install -e .
```