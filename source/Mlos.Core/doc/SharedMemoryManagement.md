# Shared Memory Management

This document provides some details about the creation and management of shared memory regions used for storing configuration settings and message channels.

## Contents

- [Shared Memory Management](#shared-memory-management)
  - [Contents](#contents)
  - [Overview](#overview)
    - [Participants](#participants)
    - [Goals](#goals)
    - [Bootstrap sequence protocol](#bootstrap-sequence-protocol)
  - [OS implementation differences](#os-implementation-differences)
    - [Linux: Anonymous Shared Memory](#linux-anonymous-shared-memory)
      - [Caveats](#caveats)
    - [Windows](#windows)
  - [Implementation details](#implementation-details)
    - [SharedMemoryMapView](#sharedmemorymapview)
    - [SharedMemoryRegionView](#sharedmemoryregionview)
  - [See Also](#see-also)

## Overview

### Participants

- *Target Process* - which holds tunable components.
- *MLOS Agent* - the agent process, responsible for collecting the telemetry and communicating with the optimizer.

### Goals

1. The *Target Process* and the *MLOS Agent* need to be able to establish an initial region of shared memory, called the *Global region*, which they will use to register smart components and manage and track additional component specific shared memory regions as necessary.

2. Each component region may need to have its own size.
Since the *MLOS Agent* is intended to be a generic/reusable helper, only the *Target Process* should need to know what those sizes are (and inform the *MLOS Agent* upon registration).
For now, the Global

3. Each process should be able to restart independently and be able to reestablish a connection to the shared memory.
For now, we assume that if both processes end, the shared memory regions should be cleaned up and the next restart will need clean regions to be recreated.
Reestablishing the contents of those shared memory regions from prior runs (e.g. initialize with old optimizer suggested values) is left as possible future work.

### Bootstrap sequence protocol

At startup the *Target Process* will check attempt check to see if the *MLOS Agent* is available to provide previously established shared memory regions.
If so, it will reuse them and the sequence is done.

Else, the *Target Process* is responsible for creating all shared memory regions and synchronization primitives.
Once it is notified that the *Mlos Agent* is available the *Target Process* can pass the shared memory region handles to the *Mlos Agent*.

Once both processes have access to the shared memory regions, message handlers can be established, additional components can be (de)registered, etc.

## OS implementation differences

OS primitives available to implement this protocol differ slightly between Windows and Linux.

### Linux: Anonymous Shared Memory

For Linux, MLOS creates *anonymous shared memory* using [`memfd_create`](https://man7.org/linux/man-pages/man2/memfd_create.2.html), and passes the corresponding file descriptor between the processes using a [Unix domain socket](https://man7.org/linux/man-pages/man7/unix.7.html) provided by the *Mlos Agent*.

This has several benefits including:

- Automatic shared memory region cleanup once all handles are closed (e.g. upon both processes exiting)
- Limited visibility in the OS
- No `/dev/shm/` file name collisions.

As mentioned above, the *Target Process* is responsible for creating the shared memory regions and channel synchronization primitives.
Once the shared memory is created, the *Target Process* will connect to the Unix socket and send the shared memory file descriptors to the *Mlos Agent*.
Once the *Mlos Agent* obtains all the required shared memory descriptors, the *Mlos Agent* will start processing shared channel messages.

On startup, the *Target Process* creates a thread which is responsible for handling *Mlos Agent* requests.
If the *Mlos Agent* restarts, it will notify the *Target Process* that it needs a list of shared memory regions.
To do this it signals a semaphore.
Upon notification, the *Target Process* reconnects to the *Mlos Agent* socket and sends the file descriptors for the shared memory region along for the *Mlos Agent* to reestablish its connection to.

Similarly, when the *Target Process* starts up, before recreating component regions, it first attempts to connect to the *Mlos Agent* via the unix socket.
If successful, it can request a list of existing shared memory regions to bootstrap its own configuration/setup process.

#### Caveats

At the moment, the name of the semaphore and socket are both well known and hardcoded.
This limits use of this pattern to one pair of cooperating *Target* and *Mlos Agent* processes at a time.

In the future we intend to provide a configuration mechanism for both processes to establish an agreed upon name/path to use (e.g. environment variable, config file, etc.).

### Windows

TODO

## Implementation details

### SharedMemoryMapView

### SharedMemoryRegionView

## See Also

- [Shared Channel](./SharedChannel.md)
