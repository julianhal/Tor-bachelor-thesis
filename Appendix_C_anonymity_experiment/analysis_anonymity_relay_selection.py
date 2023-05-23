import itertools

from rpy2.robjects.packages import importr
from rpy2.robjects.vectors import IntVector
from rpy2.robjects import r

from collections import Counter
import math
from scipy.stats import cumfreq
import numpy as np
from math import log
import json
import statistics
import csv
#from tabulate import tabulate
import re
import sys



def main():
    """
    The main() function performs the following tasks:

    1. Initializes an empty results dictionary for storing the processed data.
    2. Defines a list of parameter modification types to be analyzed.
    3. Loads the JSON data for both modified and vanilla cases for each parameter modification type.
    4. Processes the data for each modification type and updates the results dictionary.
    5. Writes the results to a CSV file named 'results.csv'.
    6. Writes the results dictionary in JSON format to a file named 'results_find_optimal_value.json' in the 'results' directory.
    """


    # Initialize results dictionary 
    results = init_results_structure()

    # Define list of parameter modification types to be analyzed
    parameter_types = ["anon_60-95"]

    # Load data for each modification type
    data = {}
    for param_type in parameter_types:
        data[param_type] = {
            'modified': load_json_data(f'./results/{param_type}_modified_data/{param_type}_modified_data.json'),
            'vanilla': load_json_data(f'./results/{param_type}_vanilla_data/{param_type}_vanilla_data.json')
        }

    # Process data and display results for each modification type
    for param_type in parameter_types:
        results = process_data(param_type, data[param_type]['modified'], data[param_type]['vanilla'], results)
        
    
    # Write results to csv file
    #write_csv(results, 'results/results.csv')

    write_anon_csv(results, 'results/results_anon.csv')

    # Write the results dictionary in json format to a file
    with open('results/results_parameteres.json', 'w') as file:
        json.dump(results, file, indent=4)



def count_relay_occurence(requests_measurements):
    # Count node occurences.
    nodes = dict()
    for circ in requests_measurements.values():
        circuit = circ["circuit"]
        if not circuit[0] in nodes:
            nodes[circuit[0]] = 1
        else:
            nodes[circuit[0]] += 1
        if not circuit[2] in nodes:
            nodes[circuit[2]] = 1
        else:
            nodes[circuit[2]] += 1
    
    return nodes

def calc_gini(requests_measurements):
    # Count node occurences.
    nodes = dict()
    for circ in requests_measurements.values():
        circuit = circ["circuit"]
        if not circuit[0] in nodes:
            nodes[circuit[0]] = 1
        else:
            nodes[circuit[0]] += 1
        if not circuit[2] in nodes:
            nodes[circuit[2]] = 1
        else:
            nodes[circuit[2]] += 1
    # Calculate Gini coefficient.
    r_stats = importr('stats')
    total = 0
    node_selection = [nodes[node] for node in nodes.keys()]
    if len(node_selection) == 0:
        return 1.0
    fdata = IntVector(node_selection)
    Fn = r_stats.ecdf(fdata)
    for nr in set(node_selection):
        cdf_x = Fn(nr)[0]
        total += cdf_x * (1 - cdf_x)
    return total / np.mean(node_selection)



def shannon_entropy(requests_measurements, filename):
    """
    Calculate the normalized Shannon entropy for entry-exit node pairs in the circuits.
    The Shannon entropy is a measure of the uncertainty or randomness in a set of data. 
    In the context of Tor circuits, it quantifies the diversity of entry-exit node pairs.
    A higher entropy value indicates a more diverse set of entry-exit node pairs.
    Args:
        requests_measurements (dict): A dictionary containing information about the Tor circuits,
                                      including the entry and exit nodes for each circuit.
        num_filtered_entry_nodes (int): The number of unique entry nodes in the filtered entry pool.
        num_filtered_exit_nodes (int): The number of unique exit nodes in the filtered exit pool.
    Returns:
        float: The normalized Shannon entropy for the entry-exit node pairs in the circuits.
    """    
    ee = {} # entry - exit

    # Open info.txt and extract the number of unique entry and exit nodes in the filtered pools
    with open(filename, 'r') as f:
        data = f.read()

    # extract the numbers of entry and exit pool
    entry_pool_match = re.search(r'Entry pool:\s*(\d+)', data)
    exit_pool_match = re.search(r'Exit pool:\s*(\d+)', data)
    num_entry_nodes = int(entry_pool_match.group(1))
    num_exit_nodes = int(exit_pool_match.group(1))

    total_filtered_pairs = num_entry_nodes * num_exit_nodes

    # Iterate through circuits and count occurrences of entry-exit node pairs
    for circ in requests_measurements.values():
        entry = circ["circuit"][0]
        exit = circ["circuit"][2]

        # Increment the count of the entry-exit pair or its reverse if it exists in the dictionary
        if (entry, exit) in ee:
            ee[(entry, exit)] += 1
        elif (exit, entry) in ee:
            ee[(exit, entry)] += 1
        else:
            # Add the new entry-exit pair to the dictionary
            ee[(entry, exit)] = 1

    # Calculate the entropy using Shannon's formula
    entropy = 0
    for count in ee.values():
        # Calculate the probability of the entry-exit pair
        probability = count / total_filtered_pairs
        # Compute the logarithm base 2 of the probability
        ld = log(probability, 2)
        # Update the entropy value according to Shannon's formula
        entropy -= probability * ld

    # Normalize the entropy value by dividing by the logarithm base 2 of the total_filtered_pairs
    shannon = entropy / log(total_filtered_pairs, 2)
    
    return shannon




# Calculate median of TTFB, Throughput, RTT, Latency
def calculate_median_without_percentiles(data, key):
    """
    Calculate the median of a list of values extracted from a dictionary, excluding the 5th and 95th percentiles.

    Args:
        data (dict): A dictionary containing data with the specified key.
        key (str): The key to extract values from the data dictionary.

    Returns:
        float: The median of the trimmed list of values.
    """
    values = [entry[key] for entry in data.values()]
    sorted_values = sorted(values)
    
    # Slice the sorted list to include values between the 5th and 95th percentiles
    length = len(sorted_values)
    lower_index = int(0.05 * length)
    upper_index = int(0.95 * length)
    trimmed_values = sorted_values[lower_index:upper_index]
    
    return np.median(trimmed_values)

def median_performance_metrics(flags_data):
    """
    Calculate the median of TTFB, Throughput, RTT, and Latency for a given dataset.

    Args:
        flags_data (dict): A dictionary containing data with keys 'ttfb', 'throughput', 'rtt', and 'latency'.

    Returns:
        tuple: A tuple containing the median values of TTFB, Throughput, RTT, and Latency.
    """

    ttfb_median = calculate_median_without_percentiles(flags_data, 'ttfb')
    throughput_median = calculate_median_without_percentiles(flags_data, 'throughput')
    rtt_median = calculate_median_without_percentiles(flags_data, 'rtt')
    latency_median = calculate_median_without_percentiles(flags_data, 'latency')
    
    # Return the calculated median values for TTFB, Throughput, RTT, and Latency
    return ttfb_median, throughput_median, rtt_median, latency_median

def calculate_percentage_increase(old_median, new_median):
    """
    Calculate the percentage increase between two values.

    Args:
        old_median (float): The old (reference) value.
        new_median (float): The new (comparison) value.

    Returns:
        float: The percentage increase between the two values.
    """
    percentage_increase = ((new_median - old_median) / old_median) * 100
    return percentage_increase

def calculate_percentage_improvements(results, parameter):
    """
    Calculate the percentage improvement for each performance metric (TTFB, Throughput, RTT, Latency) 
    between 'vanilla' and 'modified' data.

    Args:
        results (dict): A nested dictionary containing the results data for the 'vanilla' and 'modified' cases.
        parameter (str): The parameter (e.g., 'flags', 'distance', 'bandwidth', 'overload_flag', 'combined') 
                         for which the percentage improvements will be calculated.

    Returns:
        dict: The updated results dictionary with the calculated percentage improvements added.
    """
    metrics = ['ttfb', 'throughput', 'rtt', 'latency']

    for metric in metrics:
        old_median = results[parameter]["vanilla"][f"{metric}_median"]
        new_median = results[parameter]["modified"][f"{metric}_median"]

        percentage_increase = calculate_percentage_increase(old_median, new_median)
        results[parameter]["modified"][f"{metric}_%_improvement"] = percentage_increase
    return results

def init_results_structure():
    """
    Initialize a nested dictionary for storing results data.

    This function creates and returns a nested dictionary with keys for each type of
    modification (flags, distance, bandwidth, overload_flag, and combined). Each modification
    key has another dictionary with keys 'modified' and 'vanilla' for storing the corresponding
    performance data.

    Returns:
        dict: A nested dictionary with a predefined structure for storing performance data
              for different types of modifications.
    """
    return {
        "anon_60-95": {
            "modified": {},
            "vanilla": {}
    }
    }


def write_csv(results, filename):
    """
    Write the results data to a CSV file.

    This function writes the results data to a CSV file, where each row represents
    the performance of Vanilla Tor or a modified Tor version for a specific modification.
    The columns in the CSV file include 'Modification', 'Tests', 'TTFB (Kbps)', 'Throughput (Kbps)',
    'RTT (ms)', and 'Latency (ms)', along with their corresponding percentage improvement values.

    Args:
        results (dict): A dictionary containing the results data. Each key is the name
                        of a modification, and each value is another dictionary with
                        'vanilla' and 'modified' keys, each containing a dictionary with
                        the median values and percentage improvement values.

        filename (str): The name of the CSV file to write the results to.
    """
    with open(filename, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        
        headers = ['Modification', 'Tests', 'TTFB (ms)', '% Difference', 'Throughput (Kbps)', '% Difference', 'RTT (ms)', '% Difference', 'Latency (ms)', '% Difference']
        csv_writer.writerow(headers)
        
        for modification, data in results.items():
            # Round numbers
            for key, value in data.items():
                for sub_key, sub_value in value.items():
                    # Convert latency, rtt, and ttfb to milliseconds
                    if 'latency' in sub_key and 'improvement' not in sub_key \
                            or 'rtt' in sub_key and 'improvement' not in sub_key \
                            or 'ttfb' in sub_key and 'improvement' not in sub_key:
                        data[key][sub_key] = round(sub_value * 1000, 3)
                    # Convert throughput to kilobits per second
                    elif 'throughput' in sub_key:
                        data[key][sub_key] = round(sub_value / 1000, 3)
                    elif 'gini' or "shannon" in sub_key:
                        data[key][sub_key] = round(sub_value, 5)
                    # Round all other numbers to 3 decimal places
                    else:
                        data[key][sub_key] = round(sub_value, 2)

            vanilla_data = data['vanilla']
            modified_data = data['modified']
            
            csv_writer.writerow([
                modification, 'Vanilla Tor',
                vanilla_data['ttfb_median'], '',
                vanilla_data['throughput_median'], '',
                vanilla_data['rtt_median'], '',
                vanilla_data['latency_median'], ''
            ])
            
            csv_writer.writerow([
                '', modification + ' Tor',
                modified_data['ttfb_median'], modified_data['ttfb_%_improvement'],
                modified_data['throughput_median'], modified_data['throughput_%_improvement'],
                modified_data['rtt_median'], modified_data['rtt_%_improvement'],
                modified_data['latency_median'], modified_data['latency_%_improvement']
            ])

def write_anon_csv(results, filename):

    with open(filename, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        
        headers = ['Modification', 'Tests', 'Gini', 'Entropy (Shannon)']
        csv_writer.writerow(headers)
        
        for modification, data in results.items():
            print(modification)
            print(data)

            # Round numbers
            for key, value in data.items():
                for sub_key, sub_value in value.items():
                    if 'gini' in sub_key or "shannon_entropy" in sub_key:
                        data[key][sub_key] = round(sub_value, 5)

            vanilla_data = data['vanilla']
            modified_data = data['modified']
            
            csv_writer.writerow([
                modification, 'Vanilla Tor',
                vanilla_data['gini'],
                vanilla_data['shannon_entropy']
            ])
            
            csv_writer.writerow([
                '', modification + ' Tor',
                modified_data['gini'],
                modified_data['shannon_entropy']
            ])

def load_json_data(file_path):
    """Load JSON data from a file."""
    with open(file_path, 'r') as infile:
        return json.load(infile)




def process_data(modification_type, modified_data, vanilla_data, results):
    """
    Process data by calculating various metrics and percentage improvements.

    Args:
        modification_type (str): The type of modification being processed.
        modified_data (dict): The data for the modified version.
        vanilla_data (dict): The data for the vanilla version.

    Returns:
        dict: The results dictionary with calculated metrics and improvements.
    """
    # Calculate shannon entropy
    results[modification_type]["modified"]["shannon_entropy"] = shannon_entropy(modified_data, f'./results/{modification_type}_modified_data/{modification_type}_modified_data_info.txt')
    results[modification_type]["vanilla"]["shannon_entropy"] = shannon_entropy(vanilla_data, f'./results/{modification_type}_vanilla_data/{modification_type}_vanilla_data_info.txt')
    # Calculate gini coefficient
    results[modification_type]["modified"]["gini"] = calc_gini(modified_data)
    results[modification_type]["vanilla"]["gini"] = calc_gini(vanilla_data)

    relay_occurrences = count_relay_occurence(vanilla_data)

    # Write relay occurrences to a CSV file
    with open('relay_occurrences_vanilla.csv', 'w', newline='') as csvfile:
        fieldnames = ['relay', 'occurrences']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for relay, occurrences in relay_occurrences.items():
            writer.writerow({'relay': relay, 'occurrences': occurrences})

    # # Calculate median TTFB, Throughput, RTT, and Latency
    # results[modification_type]["modified"]["ttfb_median"], results[modification_type]["modified"]["throughput_median"], results[modification_type]["modified"]["rtt_median"], results[modification_type]["modified"]["latency_median"] = median_performance_metrics(modified_data)
    # results[modification_type]["vanilla"]["ttfb_median"], results[modification_type]["vanilla"]["throughput_median"], results[modification_type]["vanilla"]["rtt_median"], results[modification_type]["vanilla"]["latency_median"] = median_performance_metrics(vanilla_data)

    # Calculate percentage increase in median TTFB, Throughput, RTT, and Latency and add to results with correct parameter type
    return results #calculate_percentage_improvements(results, modification_type)


if __name__ == '__main__':
    main()