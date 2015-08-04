# HPL Tester tool
Tool for aiding in tuning the HPLinpack benchmark for HPC systems. This tool creates HPL.dat files and puts them in individual directories named by different values of N, NB, P, and Q. This tool helps determine appropriate combinations of these different numbers and creates all of the different HPL.dat files for you.

# Running on a cluster
This tool is designed to be used in conjunction with a scheduler like SLURM, in order to run the HPL benchmark with all of the various settings to see which combination creates the best flop rating.
