#!/usr/bin/env python
""" 
A tool to calculate various N and NB values for HPL and run several tests
using different combinations of them on a given set of cores/nodes/memory.
This will assume an avx2-compatible HPL program.

Usage: hpl_tool.py <nodes> <cores/node> <mem in GB>
"""
import math
import sys
import os
import subprocess
from string import Template

HPL_DAT = Template('''HPLinpack benchmark input file # 3 nodes, 72 cpus - Haswell
Innovative Computing Laboratory, University of Tennessee
HPL.out      output file name (if any)
6            device out (6=stdout,7=stderr,file)
1            # of problems sizes (N)
$N        Ns
1            # of NBs
$NB          NBs
0            PMAP process mapping (0=Row-,1=Column-major)
1            # of process grids (P x Q)
$P            Ps
$Q            Qs
16.0         threshold
1            # of panel fact
0            PFACTs (0=left, 1=Crout, 2=Right)
1            # of recursive stopping criterium
4            NBMINs (>= 1)
1            # of panels in recursion
2            NDIVs
1            # of recursive panel fact.
2            RFACTs (0=left, 1=Crout, 2=Right)
1            # of broadcast
0            BCASTs (0=1rg,1=1rM,2=2rg,3=2rM,4=Lng,5=LnM)
1            # of lookahead depth
0            DEPTHs (>=0)
2            SWAP (0=bin-exch,1=long,2=mix)
128          swapping threshold
0            L1 in (0=transposed,1=no-transposed) form
0            U  in (0=transposed,1=no-transposed) form
1            Equilibration (0=no,1=yes)
8            memory alignment in double (> 0)
''')


class HPLTool:
    """
    A class that handles creating HPL.dat files for HPLinpack based on entered
    information (nodes, cores, and memory). It creates folders for all of the 
    separate dat files and customizes each dat file based on N, NB, P, and Q
    numbers it calculates
    """
    def __init__(self, nodes, cores_per_node, mem_in_gb):
        self.nodes = nodes
        self.cores_per_node = cores_per_node
        self.mem = mem_in_gb
        self.N = int((round(math.sqrt((mem_in_gb * 1024 * 1024 * 1024 * nodes)/8))) * 0.90)
        self.total_cores = cores_per_node * nodes
        self.p = None
        self.q = None
        self.N_vals = {}
    
    def _get_all_factors(self):
        """ returns a list of all factors of self.total_cores """
        factors = []
        end = (self.total_cores // 2) + 1 # factor can't ever be more than half the number
        for i in range(1, end):
            if self.total_cores % i == 0:
                factors.append(self.total_cores // i)

        factors.append(1)
        return factors

    def _find_best_p_q(self, tuples):
        """
        Determines which pair of p/q values is best to use
        :param tuples: list of tuples containing p and q values
        :return: a tuple of the optimal p/q pair to use
        """
        best_diff = None # optimal difference between p and q
        best_tuple = None

        for tuple in tuples:
            diff = abs(tuple[0] - tuple[1]) # difference between p and q
            if best_diff == None:
                best_diff = diff
                best_tuple = tuple

            if diff < best_diff: # the current difference is better
                best_diff = diff
                best_tuple = tuple
            else: # keep current best
                continue

        return best_tuple

    def find_p_and_q_vals(self):
        """ Determines the best P and Q to use, having P <= Q """
        factors = self._get_all_factors()
        p_q = [] # will hold a list of tuples of all possible p and q combos
        for i in range(len(factors)):
            temp_p = factors[i]
            if temp_p * temp_p == self.total_cores:  # factor is a square root of the total cores
                p_q.append((temp_p, temp_p))
            for j in range(i+1, len(factors)):
                temp_q = factors[j]
                if temp_p*temp_q == self.total_cores:
                    p_q.append((temp_p, temp_q)) # append a tuple of a possible p_q combo

        best_p_q = self._find_best_p_q(p_q) # this gets the optimal combo of p and q
        if best_p_q[0] > best_p_q[1]:
            self.q = best_p_q[0] # best q
            self.p = best_p_q[1] # best p
        else:
            self.q = best_p_q[1]
            self.p = best_p_q[0]

        return (self.p, self.q)

    def optimize_N_vals(self):
        """
        for every desired NB value (eg 96, 104, 112, 120, 128), get the
        associated N value. This is just based on dividing the current value
        of N by the value of NB and then multiplying it the new N by NB.
        """
        for nb in range(96, 257, 8):
            # the nb values are NB values used to determine the final value of N
            n = self.N / nb
            optimized_n = nb * n
            self.N_vals[nb] = optimized_n


    def print_all_N_vals(self):
       print("For %s nodes, %s cores per node, and %sGB of memory per node:" % (self.nodes, 
                                                                                self.cores_per_node,
                                                                                self.mem))
       for k, v in self.N_vals.items():
           print("NB: %d    N: %d" % (k, v))

    def create_dirs_and_dats(self):
        """ 
        Creates a new directory with an apt name for each NB value and creates
        a new dat file for that combo and places the file in that directory
        """
        root_dir = "%s_nodes_%s_cores_tests" % (self.nodes, self.total_cores)
        try:
            os.mkdir(root_dir)
        except:
            print("directory '%s' already created" % root_dir)

        os.chdir(root_dir)
        for k, v in self.N_vals.items():
            dir = "NB%s_N%s_P%s_Q%s" % (k, v, self.p, self.q)
            try:
                os.mkdir(dir)
            except:
                #print("directory already created")
                pass
            os.chdir(dir)
            self.create_dat_file(v, k, self.p, self.q)
            os.chdir('../')
               
    def create_dat_file(self, n, nb, p, q):
        dat = HPL_DAT.substitute(dict(N=n, NB=nb, P=p, Q=q))
        with open('HPL.dat', 'wb') as f:
            f.write(dat)
        f.close()


class Slurm:
    # TODO: need to know how many folders there are and pass that in as the array #
    # TODO: get every line of the .dirs_list.tmp file and use SLURM_ARRAY_TASK_ID to get a line
    def __init__(self):
        # create a temp file to hold a list of all the directories
        try:
            cmd = 'ls > .dirs_list.tmp'
            popen = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            out = popen.communicate()
        except:
            print("There was an error creating the temp file directory")
            return

        sbatch = Template('''#!/bin/bash
#SBATCH --partition=$queue
#SBATCH --time=$hours:00:00
#SBATCH -o $dir/output/hpl_test_%j.log
#SBATCH --job-name=hpl_tester
#SBATCH --ntasks=$procs
#SBATCH --workdir=$dir
#SBATCH --mem=$mem

# grab line # SLURM_ARRAY_TASK_ID from dirs_list.tmp
# cd into the directory

srun xhpl
        ''')

        self.queue = "all"
        self.mem = '200'
        self.hours = '2'
        self.root_dir = os.getcwd()
        self.procs = '4'
        sbatch = sbatch.substitute(dict(cmd=cmd, queue=self.queue, mem=self.mem, hours=self.hours,
                                        procs=self.procs, dir=self.root_dir))
        print('Submitting *****{\n%s\n}*****' % sbatch)
        #popen = subprocess.Popen('sbatch', shell = True, stdin = subprocess.PIPE, stdout = subprocess.PIPE)
        #out = popen.communicate(sbatch.encode())[0].strip() #e.g. something like "Submitted batch job 209"
        #return out

if __name__ == '__main__':
    args = sys.argv[1:]
    nodes = int(args[0])
    procs = int(args[1])
    mem = int(args[2])

    hpl = HPLTool(nodes, procs, mem)
    hpl.optimize_N_vals()
    hpl.print_all_N_vals()
    print("total cores: %d" % hpl.total_cores)
    p_and_q = hpl.find_p_and_q_vals()
    print("Best P: %s" % p_and_q[0])
    print("Best Q: %s" % p_and_q[1])
    try:
        os.mkdir('test_runs')
    except:
        pass
    os.chdir('test_runs')

    hpl.create_dat_file(hpl.N_vals[128], 4, 1, 8)

    # make a new directory for every combo of N_val
    #for k, v in hpl.N_vals.items():
    #    hpl.create_dirs_and_dats()
    hpl.create_dirs_and_dats()

    slurm = Slurm()
