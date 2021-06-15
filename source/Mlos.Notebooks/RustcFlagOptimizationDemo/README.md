## Rustc Flag Optimization Demo

Author: Zack Porter  (zaporter)
2021-06-07

This project demonstrates the ability to optimize rust compliation times with MLOS. 

Directory structure:

- RustcFlagOptimization.ipynb - Jupyter notebook of the project
- RustcFlagOptimization.html - HTML rendering of the Jypyter notebook for portability reasons (2021-06-07)
- bevybench - rust benchmark to use as an example to optimize compilation with MLOS. Run via `cargo run`
- optimizer_done_1000.obj - Pickled python optimizer object after having done 1000 runs 
- observations.csv - Observations from the optimizer exported via `df.to_csv(..)`
