Experimental code accompanying the paper 
## Topological Rigidity in Satisfiability

The code is released for research and evaluation purposes only.
This repository does NOT grant a license to any patents owned by the authors.
Commercial use requires a separate patent license.

## Reproducibility

Each figure in the paper can be reproduced by directly running the corresponding script in the `src` directory.

For example:
```bash
python src/Fig2.py
```

When `Fig2.py` is executed, the figure is displayed in an interactive window.
Upon closing the window, the corresponding image file `Fig2_....png` is automatically saved to the `figures/` directory.

## Requirements

- Python 3.x
- NumPy
- Matplotlib
- A SAT solver (e.g., MiniSat) for optional verification
