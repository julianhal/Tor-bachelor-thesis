# INSTALL GUIDE

## Donload and install ubuntu 20.4.1 LTS iso
[ubuntu 20.4.1 LTS](https://ubuntu.com/download/desktop/thank-you?version=22.04.1&architecture=amd64)
```bash
sudo add-apt-repository ppa:maxmind/ppa
sudo apt update
sudo apt upgrade
```

## Install dependencies
```bash
sudo apt-get install -y \
    curl \
    git \
    cmake \
    findutils \
    libclang-dev \
    libc-dbg \
    libglib2.0-0 \
    libglib2.0-dev \
    make \
    python3 \
    python3-pip \
    python3.10-venv \
    xz-utils \
    util-linux \
    gcc \
    dstat \
    htop \
    tmux \
    g++ \
    cmake \
    libglib2.0-0 \
    libglib2.0-dev \ 
    libcurl4-openssl-dev \
    libigraph-dev \
    libgeos-dev \
    libmaxminddb0 \
    libmaxminddb-dev \
    mmdb-bin \
    r-base \
    r-base-dev \
    libssl-dev 

```

## Download python program:
```bash
git clone https://github.com/julianhal/Tor_thesis2023CISK
cd Tor_thesis2023CISK
python3 -m venv toolsenv
source toolsenv/bin/activate
pip install -r requirements.txt
```

## RESTART YOUR COMPUTER


## Build Tor from source and apply patches

## Download Tor source code
```bash
sudo apt-get install openssl libssl-dev libevent-dev build-essential automake zlib1g zlib1g-dev
git clone https://git.torproject.org/tor.git
cd tor
git checkout tor-0.4.7.13
```

### INSTALL PATCHES
**cp patches located in folder `/.../pathgen/patched_files/` to tor source code directories as written below:**

**Directory structure in tor:**
```bash
# Change the files found in this location with the patched ones
tor/src/core/or/circuitbuild.c 
tor/src/core/or/circuitbuild.h
tor/src/core/or/circuituse.c
tor/src/feature/control/control_cmd.c

# Example of patching the old circuitbuild.c found in unpatched tor
`~/.../tor/src/core/or$ cp /.../pathgen/patched_files/circuitbuild.c circuitbuild.c` 
# Do this for all the files in the list above
```

### Build and install Tor
**Go back to `~/.../tor/` and do the following commands:**
```bash
./autogen.sh
./configure --disable-asciidoc --disable-unittests --disable-manpage --disable-html-manual
make
sudo make install
```

### Configure Tor
**Create the `torrc`**
```bash
cp /usr/local/etc/tor/torrc.sample /usr/local/etc/tor/torrc
```

**Set the following options in torrc by removing the "#" before each setting:**

```
ControlPort 9051
CookieAuthentication 1
```
**Copy the code below into the torrc file, as these settings don't come as standard in the torrc:**
```bash
## Descriptors have a range of time during which they're valid. 
## To get the most recent descriptor information, regardless if Tor needs it or not, set the following.
FetchDirInfoEarly 1
FetchDirInfoExtraEarly 1source toolsenv/bin/activate

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

## Optional: Donwload Maxmind database for world relay and circuit visualization
**Download your own updated maxmind database:** (you have to create an account)
[Maxmind](https://dev.maxmind.com/geoip/geoip2/geolite2/)

1. Once logged in, download the `GeoLite2 City` in gzip format
2. Once downloaded, extract using `gunzip GeoLite2-ASN` (The filename will vary according to version)
3. Extract the tar file using `tar -xvf`
4. If you go into the folder, a file called `GeoLite2-ASN.mmdb` should be there.


## RESTART YOUR COMPUTER

# RUN GUIDE
Now you can run the program by doing the following commands:
```bash
cd Tor_thesis2023CISK
source toolsenv/bin/activate
python3 POC.py
```
