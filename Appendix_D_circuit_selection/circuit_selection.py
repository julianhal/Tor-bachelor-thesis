import time
from stem import Signal
from stem.control import Controller
import stem.process

# Socks port for Tor
SOCKS_PORT = 9050
CONNECTION_TIMEOUT = 120  # timeout before we give up on a circuit
TOR_CONTROL_IP = "127.0.0.1"
TOR_CONTROL_PORT = 9051



def print_bootstrap_lines(line):
    if "Bootstrapped" in line:
        print(line)

def measure_circuit_rtt(controller, circuit_id):
    # Measure the round-trip time (RTT) for a given circuit
    # You can implement this using a custom function that sends a payload and measures the response time
    return rtt_value

def is_unused_for_5_minutes(circuit_creation_time):
    return time.time() - circuit_creation_time > 5 * 60

# --------------------- Main ---------------------#
def main():
    tor_process = stem.process.launch_tor_with_config(
        config={
            "SocksPort": str(SOCKS_PORT),
            "ControlPort": str(TOR_CONTROL_PORT),
            "CookieAuthentication": "1",
            "FetchUselessDescriptors": "1",
            "FetchDirInfoEarly": "1",
            "FetchDirInfoExtraEarly": "1",
            "DownloadExtraInfo": "1",
            #"MaxCircuitDirtiness": "10",  # How long a circuit can be used before it is rebuilt
            #"CircuitBuildTimeout": 120
            #"LearnCircuitBuildTimeout": 0 #To keep circuit build timeouts static.
        },
        init_msg_handler=print_bootstrap_lines,
    )

    # --------------------- Tor controller ---------------------#
    # Connect to the Tor controller to get the circuit information
    try:
        # Connect to the Tor controller
        with Controller.from_port(port=TOR_CONTROL_PORT) as controller:
            controller.authenticate()

            controller.set_conf("__DisablePredictedCircuits", "1")
            """
             This line disables the creation of predicted circuits in the Tor client. 
             Predicted circuits are created in advance to reduce the latency of the first request made through the Tor network. 
             By setting this value to "1", the Tor client will no longer create these circuits.
            """

            circuit_pool = {}
            circuit_creation_times = {}

            while True:
                if len(circuit_pool) < 5:
                    # Create a new circuit and measure its RTT
                    new_circuit_id = controller.new_circuit(await_build=True)
                    new_circuit_rtt = measure_circuit_rtt(controller, new_circuit_id)

                    # Add new circuit to the pool if there's space
                    if len(circuit_pool) <= 5:
                        circuit_pool[new_circuit_id] = new_circuit_rtt
                        circuit_creation_times[new_circuit_id] = time.time()
                    else:
                        # Replace the worst circuit if the new one has a better RTT
                        worst_circuit_id = max(circuit_pool, key=circuit_pool.get)
                        if new_circuit_rtt < circuit_pool[worst_circuit_id]:
                            controller.close_circuit(worst_circuit_id)
                            del circuit_pool[worst_circuit_id]
                            del circuit_creation_times[worst_circuit_id]

                            circuit_pool[new_circuit_id] = new_circuit_rtt
                            circuit_creation_times[new_circuit_id] = time.time()

                # Close circuits unused for more than 5 minutes
                for circuit_id in list(circuit_pool.keys()):
                    if is_unused_for_5_minutes(circuit_creation_times[circuit_id]):
                        controller.close_circuit(circuit_id)
                        del circuit_pool[circuit_id]
                        del circuit_creation_times[circuit_id]

                # Select the best circuit based on RTT when needed
                best_circuit_id = min(circuit_pool, key=circuit_pool.get)
                # Use the best_circuit_id for making requests


                time.sleep(10)  # Adjust the sleep interval as needed

            # Close the Tor control port
            controller.close()

    except stem.SocketError as exc:
        print(f"Unable to connect to Tor on {TOR_CONTROL_IP}:{TOR_CONTROL_PORT}: {exc}")

    # Stop the tor process
    tor_process.stop()
