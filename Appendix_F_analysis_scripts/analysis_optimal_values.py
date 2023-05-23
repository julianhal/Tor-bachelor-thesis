import itertools
from collections import Counter
import math
import numpy as np
from math import log
from rpy2.robjects.packages import importr
from rpy2.robjects.vectors import IntVector
import json
# Import statistics Library
import statistics
import csv
from tabulate import tabulate
import os




def main():
    """
    Main function that performs the following steps:

    1. Define a dictionary containing the "steps" for each parameter type.
    2. Load JSON files for each parameter type and "steps" into a parameters dictionary.
    3. Calculate the median performance metrics for each parameter type and step and store the results in a dictionary.
    4. Print the results dictionary in a readable format.
    5. Write the results dictionary to a CSV file.

    The main function uses the following helper functions: load_json_files, create_results_dict, and write_csv.
    """

    percentiles_dict = {
        "distance": [10, 20, 30, 40, 50, 60, 70, 80, 90, 95],
        "bandwidth": [10, 20, 30, 40, 50, 60, 70, 80, 90, 92, 94, 95, 96, 98, 99],
        "flags": [0, 1],
        "overload": [0.5, 1, 3, 6, 9 ,20],
        "distance-bandwidth": ['30-30', '30-40', '30-50', '30-60', '30-70', '30-80', '30-90', '30-95', '40-30', '40-40', '40-50', '40-60', '40-70', '40-80', '40-90', '40-95', '50-30', '50-40', '50-50', '50-60', '50-70', '50-80', '50-90', '50-95', '60-30', '60-40', '60-50', '60-60', '60-70', '60-80', '60-90', '60-95', '70-30', '70-40', '70-50', '70-60', '70-70', '70-80', '70-90', '70-95', '80-30', '80-40', '80-50', '80-60', '80-70', '80-80', '80-90', '80-95', '90-30', '90-40', '90-50', '90-60', '90-70', '90-80', '90-90', '90-95']
    }

    # Define a list of parameter types
    parameter_types = ['distance', 'bandwidth', 'flags', 'overload', "distance-bandwidth"]


    # Open JSON FILES and load them into parameters dictionary
    parameters = {}
    for parameter_type in parameter_types:
        parameters[parameter_type] = load_json_files(parameter_type, percentiles_dict[parameter_type]) #steps=range(10, 80, 10))

    # Calculate the median for each parameter type and store the results in a dictionary
    results = create_results_dict(parameter_types, percentiles_dict, parameters)


    # Print top 3 of each parameter type
    for parameter_type in parameter_types:
        print(f"Top 10 {parameter_type} values:")
        top = sorted(results[parameter_type].items(), key=lambda x: x[1]["ttfb_average"], reverse=False)[:10]
        for item in top:
            print(item[0], item[1]["ttfb_median"])
        print()            



    # Write the results dictionary in json format to a file
    with open('results/results_find_optimal_value.json', 'w') as file:
        json.dump(results, file, indent=4)

    # Write the results dictionary to a CSV file
    write_csv(results, 'results/results_find_optimal_value.csv')

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
    lower_index = int(0 * length) # Change to exclude a certain percentile
    upper_index = int(1 * length) # Change to exclude a certain percentile
    trimmed_values = sorted_values[lower_index:upper_index]

    # Calculate the average of the trimmed list of values
    avg = np.average(trimmed_values)
    median = np.median(trimmed_values)
    return avg, median

def median_performance_metrics(data):
    """
    Calculate the median of TTFB, Throughput, RTT, and Latency for a given dataset.

    Args:
        flags_data (dict): A dictionary containing data with keys 'ttfb', 'throughput', 'rtt', and 'latency'.

    Returns:
        tuple: A tuple containing the median values of TTFB, Throughput, RTT, and Latency.
    """

    ttfb_median, ttfb_average = calculate_median_without_percentiles(data, 'ttfb')
    throughput_median, throughput_average = calculate_median_without_percentiles(data, 'throughput')
    rtt_median, rtt_average = calculate_median_without_percentiles(data, 'rtt')
    latency_median, latency_average = calculate_median_without_percentiles(data, 'latency')
    
    # Return the calculated median values for TTFB, Throughput, RTT, and Latency
    return ttfb_median, ttfb_average, throughput_median, throughput_average, rtt_median, rtt_average, latency_median, latency_average


def write_csv(results, output_filename):
    """
    Write the results dictionary to a CSV file.

    Args:
        results (dict): A nested dictionary containing the results data.
        output_filename (str): The name of the output CSV file.
    """
    header = ['parameter_type', 'percentile', 'ttfb_median', 'throughput_median', 'rtt_median', 'latency_median']

    with open(output_filename, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)

        # Write the header row
        csv_writer.writerow(header)

        # Write the data rows
        for parameter_type, percentiles_data in results.items():
            for percentile_key, metrics in percentiles_data.items():
                row = [
                    parameter_type,
                    percentile_key,
                    metrics['ttfb_median'],
                    metrics['throughput_median'],
                    metrics['rtt_median'],
                    metrics['latency_median']
                ]
                csv_writer.writerow(row)


def load_json_files(parameter_type, steps=range(10, 80, 10)):
    """
    Load JSON files for a given parameter_type and a range of steps.
    
    This function reads JSON files from the directory 'results' and returns a
    dictionary containing the loaded JSON objects. The input files are assumed to be
    in the format 'results/{parameter_type}_{i}_percent/{parameter_type}_{i}_percent.json', where 'i'
    is an integer from the specified steps.

    Args:
        parameter_type (str): The parameter_type for the JSON files to be loaded.
        steps (iterable, optional): An iterable of integers specifying the steps
                                     for which the JSON files will be loaded. 
                                     Default is range(0, 80, 10).
    Returns:
        dict: A dictionary containing the loaded JSON objects with keys in the format
              '{parameter_type}_{i}_percent'.
    """
    result = {}
    for i in steps:
        with open(f'results/{parameter_type}_{i}_percent/{parameter_type}_{i}_percent.json', 'r') as infile:
            result[f'{parameter_type}_{i}_percent'] = json.load(infile)
    return result



def create_results_dict(parameter_types, percentiles_dict, data):
    """
    Create a nested dictionary containing median performance metrics for each parameter type and percentile.

    Args:
        parameter_types (list): A list of parameter types (e.g., ['distance', 'bandwidth', 'flags', 'overload_flag']).
        percentiles_dict (dict): A dictionary with parameter types as keys and lists of percentiles as values.
                                (e.g., {'distance': range(0, 80, 10), 'bandwidth': range(0, 80, 10), 'flags': [0, 1], 'overload_flag': [1, 6, 9]}).
        data (dict): A dictionary containing the loaded data for each parameter type.

    Returns:
        dict: A nested dictionary with keys for each parameter type and percentile.
              Each key maps to a dictionary containing the median values of TTFB, Throughput, RTT, and Latency.
    """
    results = {}
    for parameter_type in parameter_types:
        results[parameter_type] = {}
        for percentile in percentiles_dict[parameter_type]:
            key = f"{percentile}_percent"
            results[parameter_type][key] = {}
            tmp_key = f"{parameter_type}_{percentile}_percent"
            ttfb_median, ttfb_average, throughput_median, throughput_average, rtt_median, rtt_average, latency_median, latency_average = median_performance_metrics(data[parameter_type][tmp_key])
            results[parameter_type][key]["ttfb_median"] = ttfb_median
            results[parameter_type][key]["rtt_median"] = rtt_median
            results[parameter_type][key]["latency_median"] = latency_median
            results[parameter_type][key]["throughput_median"] = throughput_median
            results[parameter_type][key]["ttfb_average"] = ttfb_average
            results[parameter_type][key]["rtt_average"] = rtt_average
            results[parameter_type][key]["latency_average"] = latency_average
            results[parameter_type][key]["throughput_average"] = throughput_average
    return results


if __name__ == "__main__":
    main()