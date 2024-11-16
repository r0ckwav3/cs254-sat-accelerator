# Sat Accelerator Project
Made for UCSB's CMPSC 254 taught by Professor Balkind

### Setup
To run this repo you will need python3.8 or above and [pyrtl](https://pyrtl.readthedocs.io/en/latest/).

We recommend that you install this via a virtual environment (although you can also use a normal pip install). In the root directory of the repo, run:
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For every subsequent time you want to activate the virtual environment, you only need to run
```
source .venv/bin/activate
```

If you want to add a new package to the project's requirements, activate the environment, pip install as usual and then run
```
pip freeze > requirements.txt
```
to update the dependancies.
