# Standard library imports
#from datetime import datetime
import datetime
import json
import re
import time
import os
# from rpy2.robjects import IntVector
# from rpy2.robjects.packages import importr
import sys

# from socket import socket as socksocket
# from SocksiPy.socks import Socks5Error, PROXY_TYPE_SOCKS5
from socks import SOCKS5Error, PROXY_TYPE_SOCKS5, socksocket

# Third-party imports
import requests
import pycurl
import io
from math import radians, sin, cos, sqrt, atan2
from re import findall
import json

# Stem imports
import stem
import stem.connection
import stem.process
import stem.socket
from stem import CircStatus
from stem import Signal
from stem.control import Controller
from stem.util import term

# MaxMind imports
import maxminddb

# --------------------- Constants ---------------------#
# socks port for Tor and pycurl
SOCKS_PORT = 9050
SOCKS_PORT_7000 = 7000

#CONNECTION_TIMEOUT = 120  # timeout before we give up on a request
TOR_CONTROL_IP = "127.0.0.1"
TOR_CONTROL_PORT = 9051

# Client latitude and longitude
CLIENT_LAT = 61.1322
CLIENT_LONG = 11.3716


# --------------------- Main ---------------------#
def main():    
    # Settings = (float %)Distance, (float %)Bandwidth, (int hours)OVERLOAD, (0/1)FLAGS, (int)NUM_REQUESTS, (int minutes)TOTAL_TIME_MINUTTES, (str)filename
    SETTINGS = (0.6, 0.95, 0.5, 1, 200, 3, "combined_60-95_modified_data")

    experiment(*SETTINGS)


# --------------------- Helper functions ---------------------#
def test_circuit(controller):
    """
    Requests a new identity from Tor to use a new circuit.
    """
    controller.signal(Signal.NEWNYM)


def print_bootstrap_lines(line):
    """
    Prints bootstrap messages in blue color.

    Args:
    - line: a line of bootstrap message
    """
    if "Bootstrapped " in line:
        print(term.format(line, term.Color.BLUE))

# --------------------- Functions used in get_top_relays() ---------------------#
def filter_out_ipv6(relays):
    """
    Filters out IPv6 addresses from the data_entry.

    Args:
    - relays: a list of relays, where each relay is a dictionary returned from Tor Metrics
    (https://metrics.torproject.org/onionoo.html)

    Returns:
    - a list of relays with only IPv4 addresses
    """
    for relay in relays:
        if "or_addresses" in relay:
            for address in relay["or_addresses"]:
                if "." in address:
                    # Filter out the port number
                    relay["ipv4_address"] = address.split(":")[0]
    return relays


def print_ipv4_to_txt_file(relays):
    """
    Prints the IPv4 addresses of all relays to a txt file and separates them by a new line.

    Args:
    - relays: a list of relays, where each relay is a dictionary returned from Tor Metrics
    (https://metrics.torproject.org/onionoo.html)
    """
    with open("./GeoIPPlotter/ipv4.txt", "w") as f:
        for relay in relays:
            f.write(relay["ipv4_address"] + "\n")


def map_ipv4_to_heatmap(relays, filename):
    """
    Maps the IPv4 addresses to a heatmap using ./GeoIPPlotter/geoipplotter.py.

    Args:
    - relays: a list of relays, where each relay is a dictionary returned from Tor Metrics
    (https://metrics.torproject.org/onionoo.html)
    - filename: the filename of the output heatmap image file

    """
    # Print the IPv4 addresses to a txt file
    print_ipv4_to_txt_file(relays)

    # Run the python script that will map the IPv4 addresses to a heatmap
    os.system(
        f"python3 ./GeoIPPlotter/geoipplotter.py -t heatmap --db ./GeoIPPlotter/GeoLite2-City_20230303.mmdb --input ./GeoIPPlotter/ipv4.txt -o ./GeoIPPlotter/heatmap_{filename}.png"
    )
    # Run the python script that will map the IPv4 addresses to a scatter map and zoom in on Europe
    os.system(
        f'python3 ./GeoIPPlotter/geoipplotter.py -t scatter --db ./GeoIPPlotter/GeoLite2-City_20230303.mmdb --input ./GeoIPPlotter/ipv4.txt -o ./GeoIPPlotter/scattermap_{filename}.png -e " -12/45/30/65"'
    )

    # Run the python script that will map the IPv4 addresses to a connection map
    # os.system('python3 ./GeoIPPlotter/geoipplotter.py -t connectionmap --db ./GeoIPPlotter/GeoLite2-City_20230303.mmdb --input ./GeoIPPlotter/ipv4.txt -o ./GeoIPPlotter/connectionmap.png -d 11.3716/61.1322')


def get_lat_long(relays):
    """
    Looks up the latitude and longitude for each relay's IPv4 address using maxmind GeoLite IP database. 
    # Download updated database from https://www.maxmind.com/en/accounts/834180/geoip/downloads

    Args:
    - relays: a list of relays, where each relay is a dictionary returned from Tor Metrics
    (https://metrics.torproject.org/onionoo.html)

    Returns:
    - a list of relays, where each relay dictionary now includes its latitude and longitude
    """
    with maxminddb.open_database(
        "./GeoIPPlotter/GeoLite2-City20230428.mmdb"
        #"./GeoIPPlotter/GeoLite2-City_20230303.mmdb"
    ) as reader:
        for relay in relays:
            address = relay["ipv4_address"]
            data = reader.get(address)
            if data != None:
                try:
                    relay["latitude"] = data["location"]["latitude"]
                    relay["longitude"] = data["location"]["longitude"]
                except:
                    pass
    return relays


def calc_distance(relays):
    """
    Calculates the distance between the client and each relay based on latitude and longitude.

    Args:
    - relays: a list of relays, where each relay is a dictionary returned from Tor Metrics
    (https://metrics.torproject.org/onionoo.html)

    Returns:
    - a list of relays, where each relay dictionary includes its distance from the client
    """
    # Earth's radius in kilometers
    R = 6373.0

    for relay in relays:
        try:
            # Convert to radians
            lat1 = radians(CLIENT_LAT)
            lon1 = radians(CLIENT_LONG)
            lat2 = radians(relay["latitude"])
            lon2 = radians(relay["longitude"])

            # Calculate the distance
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))

            # Return the distance in kilometers
            distance = R * c
            relay["distance"] = distance
        except:
            relay["distance"] = float("inf")
    return relays


def sort_relay_distances(relays):
    """
    Sorts relays by their distance from the client.

    Args:
    - relays: a list of relays, where each relay is a dictionary returned from Tor Metrics
    (https://metrics.torproject.org/onionoo.html)

    Returns:
    - a sorted list of relays by distance
    """
    sorted_relays = sorted(
        relays, key=lambda relay: relay.get("distance", float("inf"))
    )
    return sorted_relays


def filter_out_high_distance_relays(relays, distance_threshold):
    """
    Filters out relays with high distance.

    Args:
    - relays: a list of relays, where each relay is a dictionary returned from Tor Metrics
    (https://metrics.torproject.org/onionoo.html)
    - distance_threshold: a float representing the percentage of relays to be filtered out, based on distance

    Returns:
    - a list of relays, where the top distance_threshold percentage of relays have been filtered out
    """

    def remove_high_distance_relays(relays, distance_threshold):
        cutoff = int(len(relays) * (1 - distance_threshold))
        return relays[:cutoff]

    filtered_relays = remove_high_distance_relays(relays, distance_threshold)
    return filtered_relays


def sort_relays_by_bandwidth(entry_pool, middle_pool, exit_pool):
    """
    Sorts the relays in each pool by bandwidth.

    Args:
    - entry_pool: a list of entry relays
    - middle_pool: a list of middle relays
    - exit_pool: a list of exit relays

    Returns:
    - a tuple of three sorted lists of relays (one for each pool)

    """
    # Sort the relays in each pool by bandwidth
    sorted_entry_pool = sorted(
        entry_pool, key=lambda relay: relay["observed_bandwidth"], reverse=True
    )
    sorted_middle_pool = sorted(
        middle_pool, key=lambda relay: relay["observed_bandwidth"], reverse=True
    )
    sorted_exit_pool = sorted(
        exit_pool, key=lambda relay: relay["observed_bandwidth"], reverse=True
    )

    return sorted_entry_pool, sorted_middle_pool, sorted_exit_pool

def categorize_relays(relays):
    """
    Categorizes relays into entry, middle, and exit pools based on their flags.
    
    Args:
    - relays (list): a list of relays, where each relay is a dictionary returned from Tor Metrics
    
    Returns:
    - entry_pool (list): A list of relay dictionaries categorized as entry relays.
    - middle_pool (list): A list of relay dictionaries categorized as middle relays.
    - exit_pool (list): A list of relay dictionaries categorized as exit relays.
    """
    entry_pool = []
    middle_pool = []
    exit_pool = []

    for relay in relays:
        flags = relay.get("flags", [])
        # If the relay has the 'Guard' flag and not the 'Exit' flag, it's an entry relay
        if "Guard" in flags:
            entry_pool.append(relay)
        # If the relay has the 'Exit' flag and not the 'Guard' flag, it's an exit relay
        elif "Exit" in flags:
            exit_pool.append(relay)
        # If the relay has neither the 'Guard' nor the 'Exit' flag, it's a middle relay
        else:
            middle_pool.append(relay)

    return entry_pool, middle_pool, exit_pool


def filter_based_on_flags(relays):
    """
    Filters the relays based on the presence of the 'Fast' flag.
    
    Args:
    - relays (list): a list of relays, where each relay is a dictionary returned from Tor Metrics
    
    Returns:
    - fast_relays (list): A list of relay dictionaries that have the 'Fast' flag.
    """
    fast_relays = []
    for relay in relays:
        flags = relay.get("flags", [])
        if "Fast" in flags:
            fast_relays.append(relay)

    return fast_relays


def filter_out_low_bandwidth_relays(
    entry_pool, middle_pool, exit_pool, relay_bandwidth_cutoff
):
    """
    Filters out relays with low bandwidth.

    Args:
    - entry_pool: a list of entry relays
    - middle_pool: a list of middle relays
    - exit_pool: a list of exit relays
    - relay_bandwidth_cutoff: a float representing the percentage of relays to be filtered out, based on bandwidth

    Returns:
    - a tuple of three lists of relays (one for each pool: entry, middle, and exit)
    """

    # Helper function to apply the cutoff
    def apply_cutoff(pool, cutoff):
        cutoff_index = int(len(pool) * (1 - cutoff))
        return pool[:cutoff_index]

    # Apply the cutoff to each pool
    filtered_entry_pool = apply_cutoff(entry_pool, relay_bandwidth_cutoff)
    filtered_middle_pool = apply_cutoff(middle_pool, relay_bandwidth_cutoff)
    filtered_exit_pool = apply_cutoff(exit_pool, relay_bandwidth_cutoff)

    return filtered_entry_pool, filtered_middle_pool, filtered_exit_pool


def filter_by_overload_general_timestamp(entry_pool, middle_pool, exit_pool, overload):
    """
    Filters out relays that have a too recent overload_general_timestamp.

    Args:
    - entry_pool: a list of entry relays
    - middle_pool: a list of middle relays
    - exit_pool: a list of exit relays
    - overload: an integer representing the number of hours to filter out recent overload_general_timestamps

    Returns:
    - a tuple of three lists of relays (one for each pool: entry, middle, and exit)

    """

    # Filters a single relay pool based on the specified overload threshold.
    def filter_pool_overload(pool, overload):
        filtered_pool = []
        for relay in pool:
            if "overload_general_timestamp" in relay:
                current_time_millis = int(round(time.time() * 1000))
                current_time = datetime.datetime.fromtimestamp(
                    current_time_millis / 1000
                )
                X_hour_ago = current_time - datetime.timedelta(hours=overload)
                time_filter = int(round(X_hour_ago.timestamp() * 1000))

                if relay["overload_general_timestamp"] <= time_filter:
                    filtered_pool.append(relay)
            else:
                filtered_pool.append(relay)
        return filtered_pool

    filtered_entry_pool = filter_pool_overload(entry_pool, overload)
    filtered_middle_pool = filter_pool_overload(middle_pool, overload)
    filtered_exit_pool = filter_pool_overload(exit_pool, overload)

    return filtered_entry_pool, filtered_middle_pool, filtered_exit_pool

def experiment(distance, bandwidth, overload, flags, NUM_REQUESTS, TIME, filename):
    """
    This function conducts a Tor network experiment based on various parameters such as distance, bandwidth,
    overload, and flags. It creates a custom Tor network with specified entry, middle, and exit nodes,
    and then measures the performance of this network when fetching a URL multiple times.

    Args:
    - distance (float): Percentage of relays to be filtered out, based on distance
    - bandwidth (float): Percentage of relays to be filtered out, based on bandwidth
    - overload (int): Number of hours to filter out recent overload_general_timestamps
    - flags (int): Flag value to filter relays based on their flags.
    - NUM_REQUESTS (int): The number of requests to be sent during the experiment.
    - TIME (float): Time in seconds between each request.

    Returns:
    None. The function saves the results of the experiment in a JSON file and the number of failed circuits in a text file.
    """
    TIME_START = datetime.datetime.now()

    # Make pools of relays
    url = "https://onionoo.torproject.org/details"
    params = {
        "running": "true",
        "fields": "or_addresses,nickname,fingerprint,flags,country,consensus_weight,observed_bandwidth,advertised_bandwidth,exit_policy",
    }
    response_entry = requests.get(url, params=params)
    data = response_entry.json()
    relays = data["relays"]



    # Modify the relay list with distance information
    relays = filter_out_ipv6(relays)
    relays = get_lat_long(relays)
    relays = calc_distance(relays)

    # Save the total number of relays before filtering
    TOTAL_NUM_RELAYS = len(relays)


    if distance != 0: 
        relays = sort_relay_distances(relays)
        relays = filter_out_high_distance_relays(relays, distance)

    # Make plot before filtering
    # map_ipv4_to_heatmap(relays, "before_filtering")

    if flags != 0:
        relays = filter_based_on_flags(relays)
        entry_pool, middle_pool, exit_pool = categorize_relays(relays)
    else:
        entry_pool, middle_pool, exit_pool = categorize_relays(relays)
        # Split relays dict into three lists


    if bandwidth != 0:
        entry_pool, middle_pool, exit_pool = sort_relays_by_bandwidth(
            entry_pool, middle_pool, exit_pool
        )
        entry_pool, middle_pool, exit_pool = filter_out_low_bandwidth_relays(
            entry_pool, middle_pool, exit_pool, bandwidth
        )

    if overload != 0:
        entry_pool, middle_pool, exit_pool = filter_by_overload_general_timestamp(
            entry_pool, middle_pool, exit_pool, overload
        )

    # Make plot before filtering
    # map_ipv4_to_heatmap(entry_pool, "before_filtering_entry")
    # map_ipv4_to_heatmap(middle_pool, "before_filtering_middle")
    # map_ipv4_to_heatmap(exit_pool, "before_filtering_exit")


    # Get the top relay fingerprints
    top_entries_fingerprint = [relay['fingerprint'] for relay in entry_pool]
    top_middles_fingerprint = [relay['fingerprint'] for relay in middle_pool]
    top_exits_fingerprint = [relay['fingerprint'] for relay in exit_pool]
    ENTRY_FINGERPRINT = ",".join(top_entries_fingerprint)
    MIDDLE_FINGERPRINT = ",".join(top_middles_fingerprint)
    EXIT_FINGERPRINT = ",".join(top_exits_fingerprint)

    # Start Tor with the given fingerprints
    print(term.format("Starting Tor:\n", term.Attr.BOLD))
    tor_process = stem.process.launch_tor_with_config(
        config={
            "SocksPort": str(SOCKS_PORT),
            "ControlPort": str(TOR_CONTROL_PORT),
            "CookieAuthentication": "1",
            "FetchUselessDescriptors": "1",
            "FetchDirInfoEarly": "1",
            "FetchDirInfoExtraEarly": "1",
            "DownloadExtraInfo": "1",
            "CircuitBuildTimeout": "60", # Set the timeout for circuit builds to 60 seconds.
            "LearnCircuitBuildTimeout": "0", #To keep circuit build timeouts static.
            "EntryNodes": f"{ENTRY_FINGERPRINT}",
            "MiddleNodes": f"{MIDDLE_FINGERPRINT}",
            "ExitNodes": f"{EXIT_FINGERPRINT}",
        },
        init_msg_handler=print_bootstrap_lines,
    )

if __name__ == "__main__":
    main()

