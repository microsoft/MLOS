# Shared Memory Management

# Bootstrap sequence

# Overview

Target process, process which hold tunable components.

MLOS Agent - the agent process, responsible for collecting the telemetry and communicating with the optimizer.

## OS implementation differences.

MLOS is handling shared memory differently on Windows and Linux.

Linux is creating anonymous shared memory, and it is passing a file descriptor between the processes using [Unix domain socket](https://man7.org/linux/man-pages/man7/unix.7.html).

The target process is responsible for creating shared memory regions and channel synchronization primitives.
Once the shared memory is created, the target process will connect to the Unix socket and sends the shared memory file
descriptors. Once the agent obtains all the required shared memory descriptors, the agent will start processing shared channel messages.

On startup, the target process creates a thread which is responsible for handling agent request.
If the agent restarts, it will notify the target process that it needs a list of file descriptors once the target process reconnects to the socket.

## Implementation details

### SharedMemoryMapView

### SharedMemoryRegionView

