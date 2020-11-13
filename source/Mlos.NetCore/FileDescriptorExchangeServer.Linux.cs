// -----------------------------------------------------------------------
// <copyright file="FileDescriptorExchangeServer.Linux.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Sockets;
using System.Threading;

using Mlos.Core.Internal;

namespace Mlos.Core.Linux
{
    internal struct AnonymousSharedMemory
    {
        internal IntPtr SharedMemoryFd;

        internal ulong SharedMemorySize;
    }

    /// <summary>
    /// FileDescriptor exchange server.
    /// </summary>
    public class FileDescriptorExchangeServer : IDisposable
    {
        private readonly Dictionary<MemoryRegionId, AnonymousSharedMemory> fileDescriptors = new Dictionary<MemoryRegionId, AnonymousSharedMemory>();

        private readonly string socketName;

        private readonly string semaphoreName;

        private Socket serverSocket;

        /// <summary>
        /// Initializes a new instance of the <see cref="FileDescriptorExchangeServer"/> class.
        /// </summary>
        /// <param name="socketName"></param>
        /// <param name="semaphoreName"></param>
        public FileDescriptorExchangeServer(string socketName, string semaphoreName)
        {
            this.socketName = socketName;
            this.semaphoreName = semaphoreName;
        }

        /// <summary>
        /// Handle requests.
        /// </summary>
        public void HandleRequests()
        {
            File.Delete(socketName);

            serverSocket = new Socket(AddressFamily.Unix, SocketType.Stream, ProtocolType.Unspecified);

            // Start listening on the Unix socket.
            //
            serverSocket.Bind(new UnixDomainSocketEndPoint(socketName));
            serverSocket.Listen(backlog: 1);

            // Signal the target process, the Agent is ready.
            //
            using NamedEvent namedEvent = NamedEvent.CreateOrOpen(semaphoreName);
            namedEvent.Signal();
            {
                // Accept the connection and obtain the list of the shared memory regions.
                //
                using Socket acceptedSocket = serverSocket.Accept();
                HandleAcceptedRequest(acceptedSocket);
            }

            Thread handlerThread = new Thread(
                start: () =>
                {
                    while (!isDisposed)
                    {
                        Socket socket = serverSocket;
                        if (socket == null)
                        {
                            // Stop processing the request after we disposed the socket.
                            //
                            break;
                        }

                        try
                        {
                            using Socket acceptedSocket = socket.Accept();
                            HandleAcceptedRequest(acceptedSocket);
                        }
                        catch (SocketException)
                        {
                            // Ignore the exception.
                            //
                        }
                        catch (ObjectDisposedException)
                        {
                            // Ignore the exception.
                            //
                        }
                    }
                });

            handlerThread.Start();
        }

        /// <summary>
        /// Handle request.
        /// </summary>
        /// <param name="acceptedSocket"></param>
        private void HandleAcceptedRequest(Socket acceptedSocket)
        {
            try
            {
                while (true)
                {
                    FileDescriptorExchangeMessage msg = default;
                    acceptedSocket.ReceiveMessageAndFileDescriptor(ref msg, out IntPtr sharedMemoryFd);

                    if (msg.ContainsFd)
                    {
                        // Store received file descriptor in the dictionary.
                        //
                        fileDescriptors.Add(
                            msg.MemoryRegionId,
                            new AnonymousSharedMemory
                            {
                                SharedMemoryFd = sharedMemoryFd,
                                SharedMemorySize = msg.MemoryRegionSize,
                            });
                    }
                    else
                    {
                        if (fileDescriptors.ContainsKey(msg.MemoryRegionId))
                        {
                            AnonymousSharedMemory sharedMemory = fileDescriptors[msg.MemoryRegionId];
                            msg.ContainsFd = true;
                            msg.MemoryRegionSize = sharedMemory.SharedMemorySize;

                            acceptedSocket.SendMessageAndFileDescriptor(
                                ref msg,
                                sharedMemory.SharedMemoryFd);
                        }
                        else
                        {
                            // Replay we do not have require memory region.
                            //
                            msg.ContainsFd = false;
                            acceptedSocket.SendMessageAndFileDescriptor(
                                ref msg,
                                IntPtr.Zero);
                        }
                    }
                }
            }
            catch
            {
                // #TODO verify is disconnected
                //
            }
        }

        /// <summary>
        /// Returns file descriptor for given memory region id.
        /// </summary>
        /// <param name="memoryRegionId"></param>
        /// <returns></returns>
        public IntPtr GetSharedMemoryFd(MemoryRegionId memoryRegionId)
        {
            return fileDescriptors[memoryRegionId].SharedMemoryFd;
        }

        /// <summary>
        /// Returns memory region size for given memory region id.
        /// </summary>
        /// <param name="memoryRegionId"></param>
        /// <returns></returns>
        public ulong GetSharedMemorySize(MemoryRegionId memoryRegionId)
        {
            return fileDescriptors[memoryRegionId].SharedMemorySize;
        }

        /// <summary>
        /// Protected implementation of Dispose pattern.
        /// </summary>
        /// <param name="disposing"></param>
        protected virtual void Dispose(bool disposing)
        {
            if (isDisposed || !disposing)
            {
                return;
            }

            // Close the socket.
            //
            serverSocket?.Disconnect(reuseSocket: false);
            serverSocket?.Close();
            serverSocket?.Dispose();
            serverSocket = null;

            isDisposed = true;
        }

        /// <inheritdoc/>
        public void Dispose()
        {
            // Dispose of unmanaged resources.
            //
            Dispose(true);

            // Suppress finalization.
            //
            GC.SuppressFinalize(this);
        }

        private bool isDisposed;
    }
}
