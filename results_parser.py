'''
Parses all output files after slurm array is finished running to determine the best
HPL options for a given configuration
'''

__author__ = 'Mike Gilbert'

import os
import linecache
from operator import itemgetter

TEST_RUNS_DIR = os.path.join(os.getcwd(), 'test_runs')
OUTPUT_DIR = 'output'

class HPLParser:

    def get_output_data(self):
        os.chdir(TEST_RUNS_DIR)
        unique_config_dirs = os.listdir('.')
        all_results = {} # will look like {'1_node_2_cores': [], '2_nodes_4_cores': []}
        for dir in unique_config_dirs:
            flops_results = []
            os.chdir(dir)
            output_files = os.listdir(OUTPUT_DIR)

            for file in output_files:
                results_line = linecache.getline(os.path.join(OUTPUT_DIR, file), 49)
                results = results_line.split()
                print(results)
                d = {
                    'N': results[1],
                    'NB': results[2],
                    'Time': results[5],
                    'Gflops': results[6],
                    'gflop_float': float(results[6].split('e')[0])
                }
                flops_results.append(d)
            all_results[dir] = flops_results # dict key is directory name and value is list of results
            os.chdir('../')

        return all_results

    def get_best_flops(self, flops_results):
        best = 0
        best_result = {}
        for result in flops_results:
            temp = result['gflop_float']
            if temp > best:
                best = temp
                best_result = result
        
        return best_result

    def sort(self, list, key):
        sorted_results = sorted(list, key=itemgetter(key), reverse=True)
        return sorted_results

    def print_all_to_file(self, file_name, all_results):
        with open(file_name, 'wb') as f:
            for dir, results in all_results:
                f.write("**************************\n")
                f.write(dir + "\n")
                f.write("**************************\n\n")
                # get and print out best results for this directory
                best = self.get_best_flops(results)
                f.write("Best result:\n")
                for k, v in best.items():
                    if k == 'gflop_float':
                        continue
                    f.write(k + ": " + v + "  \n")
                f.write("\n\n")
                # sort and print out all the rest of the results
                f.write("All results:\n")
                sorted_results = self.sort(results, 'gflop_float')
                for result in sorted_results:
                    for k,v in result.items():
                        if k == 'gflop_float':
                            continue
                        f.write(k + ":  " + v + "  ")
                    f.write("\n")

        f.close()

if __name__ == '__main__':
    parser = HPLParser()
    all_results = parser.get_output_data()
    parser.print_all_to_file('test_results.txt', all_results)

