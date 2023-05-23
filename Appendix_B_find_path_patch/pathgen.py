# -*- coding: utf-8 -*-
"""
https://github.com/ohyicong/Tor/blob/master/create_advanced_tor_proxy.py
"""
import io
import os
import stem.process
from stem.control import Controller
from stem import Signal
from stem import CircStatus
import stem.connection
import stem.process
import stem.socket
from stem import CircStatus
from stem import Signal
from stem.control import Controller
from stem.util import term
import json
from datetime import datetime
import time
import sys
import sys
from argparse import ArgumentParser
from re import findall
from pkg_resources import get_distribution
from stem.control import Controller, EventType
from stem.connection import connect_port
from stem.version import Version

import io
import time
import pycurl


def print_bootstrap_lines(line):
    if "Bootstrapped " in line:
        print(term.format(line, term.Color.BLUE))


def query(url):
  """
  Uses pycurl to fetch a site using the proxy on the SOCKS_PORT.
  """

  output = io.BytesIO()

  query = pycurl.Curl()
  query.setopt(pycurl.URL, url)
  query.setopt(pycurl.PROXY, 'localhost')
  query.setopt(pycurl.PROXYPORT, SOCKS_PORT)
  query.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5_HOSTNAME)
  query.setopt(pycurl.CONNECTTIMEOUT, CONNECTION_TIMEOUT) # Remove if necessary
  query.setopt(pycurl.WRITEFUNCTION, output.write)

  try:
    query.perform()
    return output.getvalue()
  except pycurl.error as exc:
    return "Unable to reach %s (%s)" % (url, exc)


def scan(controller, path):
  """
  Fetch check.torproject.org through the given path of relays, providing back
  the time it took.
  """

  # path = [Entrynode, exitnode]
  circuit_id = controller.new_circuit(path, await_build = True) # CREATE CIRCUIT

  def attach_stream(stream):
    if stream.status == 'NEW':
      controller.attach_stream(stream.id, circuit_id)

    controller.add_event_listener(attach_stream, stem.control.EventType.STREAM)

  try:
    controller.set_conf('__LeaveStreamsUnattached', '1')  # leave stream management to us
    start_time = time.time()

    # https://example.com/
    # check_page = query('https://check.torproject.org/')
    check_page = query('https://example.com/')

    # if 'This domain is for use in illustrative examples in documents.' not in check_page:
    #   raise ValueError("Request didn't have the right content")

    return time.time() - start_time
  finally:
    controller.remove_event_listener(attach_stream)
    controller.reset_conf('__LeaveStreamsUnattached')


# socks port for Tor
SOCKS_PORT = 9050
SOCKS_PORT = 7000

CONNECTION_TIMEOUT = 120  # timeout before we give up on a circuit
TOR_CONTROL_IP = "127.0.0.1"
TOR_CONTROL_PORT = 9051

print(term.format("Starting Tor:\n", term.Attr.BOLD))

tor_process = stem.process.launch_tor_with_config(
    config={
        "SocksPort": str(SOCKS_PORT),
        "ControlPort": str(TOR_CONTROL_PORT),
        "CookieAuthentication": "1",
        "FetchUselessDescriptors": "1",
        "FetchDirInfoEarly": "1",
        "FetchDirInfoExtraEarly": "1",
        "DownloadExtraInfo": "1"
    },
    init_msg_handler=print_bootstrap_lines,
)



# --------------------- Tor controller ---------------------#
# Connect to the Tor controller to get the circuit information
try:
    # Connect to the Tor controller
    with Controller.from_port(port=TOR_CONTROL_PORT) as controller:
        controller.authenticate()


        # Change guard nodes for every path.
        msg = controller.msg('DROPGUARDS')
        assert msg.is_ok(), ("DUMPGUARDS command failed with error " +
                            "'%s'. Is your tor client patched?\n" % str(msg))

        # Get a path from tor.
        msg = controller.msg('FINDPATH')
        assert msg.is_ok(), ("FINDPATH command failed with error " +
                            "'%s'. Is your tor client patched?\n" % str(msg))

        relay_fingerprints = findall('[A-Z0-9]{40}', str(msg))
        time_taken = scan(controller, relay_fingerprints)
        print('%s => %0.2f seconds' % (relay_fingerprints, time_taken))



        # Close the Tor control port
        controller.close()

except stem.SocketError as exc:
    print(f"Unable to connect to Tor on {TOR_CONTROL_IP}:{TOR_CONTROL_PORT}: {exc}")



# Stop the tor process
tor_process.terminate()
tor_process.wait()