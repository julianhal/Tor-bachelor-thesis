import itertools
from collections import Counter
import math
import numpy as np
from math import log
# from rpy2.robjects.packages import importr
# from rpy2.robjects.vectors import IntVector
import json
import statistics
import csv
from tabulate import tabulate
import re
import sys
from scipy.stats import ttest_rel
import matplotlib.pyplot as plt
import seaborn as sns

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
    parameter_types = ['distance', 'bandwidth', 'flags', 'overload', "combined_60-95"] #, "combined_40-40", "combined_80-40", "combined_30-95", "combined_80-80"]

    # Load data for each modification type
    data = {}
    for param_type in parameter_types:
        data[param_type] = {
            'modified': load_json_data(f'./results/{param_type}_modified_data/{param_type}_modified_data.json'),
            'vanilla': load_json_data(f'./results/{param_type}_vanilla_data/{param_type}_vanilla_data.json')
        }

    # Process data and display results for each modification type
    for param_type in parameter_types:
        print(f'Processing {param_type} data...')
        results = process_data(param_type, data[param_type]['modified'], data[param_type]['vanilla'], results)

    # Write the results dictionary in json format to a file
    with open('results/results_parameteres.json', 'w') as file:
        json.dump(results, file, indent=4)    

    write_p_values_csv(results, 'results/p_values.csv')

    # Write results to csv file
    write_csv(results, 'results/results.csv')




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
        "flags": {
            "modified": {},
            "vanilla": {}
        },
        "distance": {
            "modified": {},
            "vanilla": {}
        },
        "bandwidth": {
            "modified": {},
            "vanilla": {}
        },
        "overload": {
            "modified": {},
            "vanilla": {}
        },
        "combined_60-95": {
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
            for key, value in data.items():
                if key not in ['vanilla', 'modified']: # Skip the p values
                    continue
                for sub_key, sub_value in value.items():
                    # Convert latency, rtt, and ttfb to milliseconds
                    if 'latency' in sub_key and 'improvement' not in sub_key \
                            or 'rtt' in sub_key and 'improvement' not in sub_key \
                            or 'ttfb' in sub_key and 'improvement' not in sub_key:
                        data[key][sub_key] = round(sub_value * 1000, 3)
                    # Convert throughput to kilobits per second
                    elif 'throughput' and 'improvement' not in sub_key:
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



def write_p_values_csv(results, filename):
    """
    Write the p-values from the results data to a CSV file.

    Args:
        results (dict): A dictionary containing the results data. Each key is the name
                        of a modification, and each value is another dictionary with
                        'vanilla', 'modified', and p-value keys.
        filename (str): The name of the CSV file to write the p-values to.
    """
    with open(filename, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)

        # Write the header row
        headers = ['Modification', 'Metric', 'P-Value']
        csv_writer.writerow(headers)

        # Loop through the results dictionary and write the p-values to the CSV file
        for modification, data in results.items():
            for key, value in data.items():
                if '_p_value' in key:
                    csv_writer.writerow([modification, key, value])




def load_json_data(file_path):
    """Load JSON data from a file."""
    with open(file_path, 'r') as infile:
        return json.load(infile)


def perform_t_tests(modified_data, vanilla_data):
    metrics = ['ttfb', 'throughput', 'rtt', 'latency']
    p_values = {}

    for metric in metrics:
        modified_values = [entry[metric] for entry in modified_data.values()]
        vanilla_values = [entry[metric] for entry in vanilla_data.values()]
        
        # # Print length of each list
        # print(f"Modified {metric} values: {len(modified_values)}")
        # print(f"Vanilla {metric} values: {len(vanilla_values)}")

        t_statistic, p_value = ttest_rel(modified_values, vanilla_values)
        p_values[f"{metric}_p_value"] = p_value

    return p_values



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

    # Calculate median TTFB, Throughput, RTT, and Latency
    results[modification_type]["modified"]["ttfb_median"], results[modification_type]["modified"]["throughput_median"], results[modification_type]["modified"]["rtt_median"], results[modification_type]["modified"]["latency_median"] = median_performance_metrics(modified_data)
    results[modification_type]["vanilla"]["ttfb_median"], results[modification_type]["vanilla"]["throughput_median"], results[modification_type]["vanilla"]["rtt_median"], results[modification_type]["vanilla"]["latency_median"] = median_performance_metrics(vanilla_data)

    # Calculate p-values for TTFB, Throughput, RTT, and Latency
    p_values = perform_t_tests(modified_data, vanilla_data)

    # Add p-values to the results dictionary
    results[modification_type].update(p_values)

    # Calculate percentage increase in median TTFB, Throughput, RTT, and Latency and add to results with correct parameter type
    return calculate_percentage_improvements(results, modification_type)


if __name__ == '__main__':
    main()