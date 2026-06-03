# pythong

A French-Riviera-compatible alternative to Python. Still needs Python to work.

Pythong-cong started as a joke, and it obviously still is one. It is a very simple python-based programming language, that remaps Python keywords to reflect a more south-of-France oriented vocabulary.

The Pythong-cong team had the opportunity to try and implement a complete interpreter themselves but they obviously did not : running a .cong file just transpiles it into python in-memory for the python interpreter to run. This choice was first regarded as a catastrophic design performance-wise, but then again, that's python ecosystem for you.

## Features


Aren't you tired of writing this kind of crap:

```
    try:
        with open("nonexistent.txt") as f:
            data = f.read()
    except FileNotFoundError:
        pass
    except OSError as e:
        raise RuntimeError("unexpected") from e
```

When you could hand this glorious piece of code to your beloved team for review?
```
    essayong  :
        quangtia open("nonexistent.txt") kiéle f:
            data = f.read()
    cartong FileNotFoundCaguade:
        allezva 
    cartong OSCaguade kiéle e:
        siffle RuntimeCaguade("unexpected") fouillang e 
```

## Install

```bash
pip install -e .
```

## Usage

```bash
pythong-cong tentatchives/test1.cong          # run a .cong program
pythong-traductiong tentatchives/test1.py     # translate .py -> .cong
```
