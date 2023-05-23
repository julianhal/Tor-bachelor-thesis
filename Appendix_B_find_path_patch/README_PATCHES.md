
# INTRO 
This is a folder containing the `FINDPATH` patch for Tor, which allows you to get the path of a circuit in python using Tor's built in path generation algorithm. This is useful for testing and debugging purposes, as it allows you to get the path of a circuit without having to use the Tor network. In our thesis we use this patch to generate paths and then manually control circuit building.

These patches are based on the following patch by **Robert Annessi** <robert.annessi@nt.tuwien.ac.at>: [LINK](https://github.com/naviga-tor/navigator/blob/master/patches/tor-findpath.patch).
His patch was for Tor version, 0.2.3.x. 
We have modified the patch to work with the newest Tor version 0.4.7.13. 

## Files
- In the file `findpath.patch` you can find the diffrences between the orginal files in from Tor source code version 0.4.7.13 and the modified files for the `findpath` patch.
- In the `patched_files` you can find the modified files.
- In the file `pathgen.py` you can find a python script, which illustrates the patches and how to use them.  

## Differences between the original and modified files:

1. `circuitbuild.c`:
   - `circuit_list_path_impl` function: Changed `static char *` to `char *`
   - `onion_populate_cpath` function: Changed `static int` to `int`
   - `onion_pick_cpath_exit` function: Changed `STATIC int` to `int`

2. `circuitbuild.h`:
   - Added function declaration: `char *circuit_list_path_impl(origin_circuit_t *circ, int verbose, int verbose_names)`
   - Added function declaration: `int onion_populate_cpath(origin_circuit_t *circ)`
   - Changed comment: `//int onion_pick_cpath_exit(origin_circuit_t *circ, extend_info_t *exit)`
   - `onion_pick_cpath_exit` function: Changed `STATIC int` to `int`

3. `circuituse.c`:
   - Changed constant value: `#define MAX_CIRCUIT_FAILURES 1000` (previously 5)

4. `control_cmd.c`:
   - Added include: `//#include "core/or/crypt_path_st.h"`
   - Added `control_cmd_syntax_t findpath_syntax`
   - Added function `handle_control_findpath(control_connection_t *conn, const control_cmd_args_t *args)`
   - Added `ONE_LINE(findpath, 0)` to the list of commands



## Build Tor from source and apply patches
```bash
sudo apt-get install openssl libssl-dev libevent-dev build-essential automake zlib1g zlib1g-dev
git clone https://git.torproject.org/tor.git
cd tor
git checkout tor-0.4.7.13
```
### **INSTALL PATCHES**
cp patches located in folder `/.../pathgen/patched_files/` to tor source code directories as written below:

Directory structure in tor:
```bash
# Change the files found in this location with the patched ones
tor/src/core/or/circuitbuild.c 
tor/src/core/or/circuitbuild.h
tor/src/core/or/circuituse.c
tor/src/feature/control/control_cmd.c

# Example of patching the old circuitbuild.c found in unpatched tor
~/.../tor/src/core/or$ cp /.../pathgen/patched_files/circuitbuild.c circuitbuild.c
```

Go back to `~/.../tor/` and do the following commands:
```bash
./autogen.sh
./configure --disable-asciidoc --disable-unittests --disable-manpage --disable-html-manual
make
sudo make install
```

Create the `torrc`
```bash
cp /usr/local/etc/tor/torrc.sample /usr/local/etc/tor/torrc
```

## Configure torrc
Set the following options in torrc by removing the "#" before each setting:

```
ControlPort 9051
CookieAuthentication 1
```
Copy the code below into the torrc file, as these settings don't come as standard in the torrc:

```bash
## Descriptors have a range of time during which they're valid. 
## To get the most recent descriptor information, regardless if Tor needs it or not, set the following.
FetchDirInfoEarly 1
FetchDirInfoExtraEarly 1

## Tor doesn't need all descriptors to function. In particular...
##
##  * Tor no longer downloads server descriptors by default, opting
##    for microdescriptors instead.
##
##  * If you aren't actively using Tor as a client then Tor will
##    eventually stop downloading descriptor information altogether
##    to relieve load on the network.
##
## To download descriptors regardless of if they're needed by the
## Tor process or not set...

FetchUselessDescriptors 1

## Tor doesn't need extrainfo descriptors to work. If you want Tor to download
## them anyway then set...

DownloadExtraInfo 1
```

