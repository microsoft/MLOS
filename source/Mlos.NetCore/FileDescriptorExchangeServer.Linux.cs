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
using System.Text;
using System.Threading;

using Mlos.Core.Internal;

namespace Mlos.Core.Linux
{
    /// <summary>
    /// FileDescriptor exchange server.
    /// </summary>
    public sealed class FileDescriptorExchangeServer : IDisposable
    {
        private readonly Dictionary<string, IntPtr> fileDescriptors = new Dictionary<string, IntPtr>();

        private readonly string socketFolderPath;

        private Socket serverSocket;

        /// <summary>
        /// Initializes a new instance of the <see cref="FileDescriptorExchangeServer"/> class.
        /// </summary>
        /// <param name="socketFolderPath"></param>
        public FileDescriptorExchangeServer(string socketFolderPath)
        {
            this.socketFolderPath = socketFolderPath;
        }

        /// <summary>
        /// Handle requests.
        /// </summary>
        public void HandleRequests()
        {
            // Ensure the folder containing the socket file is created.
            //
            Directory.CreateDirectory(socketFolderPath);

            string socketName = Path.Combine(socketFolderPath, "mlos.sock");
            string openFilePath = Path.Combine(socketFolderPath, "mlos.opened");

            // Unix domain sockets (AF_UNIX) does not support SO_REUSEADDR, unlink the file.
            //
            _ = Native.FileSystemUnlink(socketName);

            serverSocket = new Socket(AddressFamily.Unix, SocketType.Stream, ProtocolType.Unspecified);

            // Start listening on the Unix socket.
            //
            serverSocket.Bind(new UnixDomainSocketEndPoint(socketName));

            serverSocket.Listen(backlog: 1);

            // Create or update the opened socket file,
            // to signal the target process that the agent is ready to receive the file descriptors.
            //
            File.WriteAllText(openFilePath, string.Empty);
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
                    int receivedLength = acceptedSocket.ReceiveMessageAndFileDescriptor(
                        out byte[] messageBuffer,
                        out var sharedMemoryFd);

                    if (receivedLength == 0)
                    {
                        // Disconnected.
                        //
                        return;
                    }

                    string sharedMemoryName = Encoding.ASCII.GetString(messageBuffer);

                    if (sharedMemoryFd != Native.InvalidPointer)
                    {
                        // Store received file descriptor in the dictionary.
                        //
                        lock (fileDescriptors)
                        {
                            fileDescriptors.Add(sharedMemoryName, sharedMemoryFd);
                        }
                    }
                    else
                    {
                        lock (fileDescriptors)
                        {
                            if (fileDescriptors.ContainsKey(sharedMemoryName))
                            {
                                sharedMemoryFd = fileDescriptors[sharedMemoryName];
                            }
                        }

                        FileDescriptorExchangeMessage msg = default;

                        acceptedSocket.SendMessageAndFileDescriptor(
                            ref msg,
                            sharedMemoryFd);
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
        /// <param name="sharedMemoryName"></param>
        /// <returns></returns>
        internal IntPtr GetSharedMemoryFd(string sharedMemoryName)
        {
            lock (fileDescriptors)
            {
                return fileDescriptors[sharedMemoryName];
            }
        }

        /// <summary>
        /// Implementation of Dispose pattern.
        /// </summary>
        /// <param name="disposing"></param>
        private void Dispose(bool disposing)
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
        }

        private bool isDisposed;
    }
}
