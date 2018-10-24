# BGP Policy Analysis - "Symbolic Execution"
Hanjing Gao's Semester Thesis


## Setup

1. Create a virtual environment with python 3. This
[link](https://stackoverflow.com/questions/50239773/how-to-get-virtualenv-to-run-python-3-instead-of-python-2-7)
might help.

2. Activate the virtual environment, by running
`source VENVNAME/bin/activate`. Don't forget to replace `VENVNAME` with
the actual name of your virtual environment.

3. Install all required packages using the provided `requirements.txt` file.
Simply run `pip install -r requirements.txt` in the virtual environment.

## Running the script

Use the provided CLI:

```bash
$ python run_analysis.py
```

Then, first load a network model by issuing the command `load`. After,
you can run the symbolic propagation of the announcements by issuing
`run`.
