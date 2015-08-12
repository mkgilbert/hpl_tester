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

        for dir in unique_config_dirs:
            self.flops_results = []
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
                self.flops_results.append(d)

        return self.flops_results

    def get_best_flops(self):
        best = 0
        self.best_result = {}
        for result in self.flops_results:
            temp = result['gflop_float']
            if temp > best:
                best = temp
                self.best_result = result
        
        return self.best_result

    def sort(self, list, key):
        self.sorted_results = sorted(list, key=itemgetter(key), reverse=True)        
        return self.sorted_results

    def print_all_to_file(self, file_name):
        with open(file_name, 'wb') as f:
            f.write("Best result:\n")
            for k,v in self.best_result.items():
                if k == 'gflop_float':
                    continue
                f.write(k + ": " + v + "  \n")
            f.write("\n\n")
            f.write("All results:\n")    
            for result in self.sorted_results:
                for k,v in result.items():
                    if k == 'gflop_float':
                        continue
                    f.write(k + ":  " + v + "  ")
                f.write("\n")

        f.close()

if __name__ == '__main__':
    parser = HPLParser()
    parser.get_output_data()
    parser.get_best_flops()
    parser.sort(parser.flops_results, 'gflop_float')
    parser.print_all_to_file('test_results.txt')

