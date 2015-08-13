# HPL Tester tool
Tool for aiding in tuning the HPLinpack benchmark for HPC systems. This tool creates HPL.dat files and puts them in individual directories named by different values of N, NB, P, and Q. This tool helps determine appropriate combinations of these different numbers and creates all of the different HPL.dat files for you.

## Running on a cluster
This tool is designed to be used in conjunction with  SLURM, in order to run the HPL benchmark with all of the various settings to see which combination creates the best flop rating.

## How to Run
*Python 2 only*

1. Make sure hpl-2.1 is unpacked into the directory above the root directory of this repository (So that hpl-2.1 and hpl_tester directories are side-by-side).
2. Make sure you have the correct mpi libraries in your path - They must be the same that you built hpl with (Just do `module load intel-mpi/5.0`)
3. Run the hpl_tester.py from inside the hpl_tester directory. It takes 3 arguments that are required: number of nodes, number of processors per node, and memory per node in GB, with an optional --time argument.
  Example:
  ```$ python hpl_tester.py --nodes=3 --procs=16 --mem=30 --time=24```
  The above example would run xhpl on 3 nodes, and 16 procs per node with 30 GB per node. This would be a total of 48 tasks running on the server with a time limit of 24 hours.
4. Check the output for each run inside the 'test_runs/<your_specs>/output' directory.
5. running 'python parse_results.py' will automatically go through your output directory and print the sorted results to test_runs/test_results.txt.
