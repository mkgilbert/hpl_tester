'''
Parses all output files after slurm array is finished running to determine the best
HPL options for a given configuration
'''

__author__ = 'Mike Gilbert'

import os
import linecache

TEST_RUNS_DIR = os.path.join(os.getcwd(), 'test_runs')

class HPLParser:

    def get_output_dirs(self):
        os.chdir(TEST_RUNS_DIR)
        unique_config_dirs = os.listdir('.')

        for dir in unique_config_dirs:
            flops_results = []
            os.chdir(dir)
            output_files = os.listdir('output')

            for file in output_files:
                results_line = linecache.getline(os.path.join('output', file), 48)
                results = results_line.split(' ')
                d = {
                    'N': results[1],
                    'NB': results[2],
                    'Time': results[5],
                    'Gflops': results[6]
                }
                flops_results.append(d)

        with open('test_results', 'wb') as f:
            for result in flops_results:
                for k,v in result:
                    f.write(k + "  " + v)
                f.write("\n")

        f.close()

if __name__ == '__main__':
    parser = HPLParser()
    parser.get_output_dirs()