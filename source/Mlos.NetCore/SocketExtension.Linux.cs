// -----------------------------------------------------------------------
// <copyright file="SocketExtension.Linux.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Net.Sockets;
using System.Runtime.InteropServices;

namespace Mlos.Core.Linux
{
    /// <summary>
    /// Socket extension class.
    /// </summary>
    public static class SocketExtension
    {
        /// <summary>
        /// Receives the message and passed file descriptor.
        /// </summary>
        /// <param name="socket"></param>
        /// <param name="buffer"></param>
        /// <param name="fileDescriptor"></param>
        /// <returns></returns>
        internal static int ReceiveMessageAndFileDescriptor(
            this Socket socket,
            out byte[] buffer,
            out IntPtr fileDescriptor)
        {
            if (socket == null)
            {
                throw new ArgumentNullException(nameof(socket));
            }

            fileDescriptor = Native.InvalidPointer;
            buffer = null;

            unsafe
            {
                Span<byte> messageSpan = stackalloc byte[256];

                fixed (byte* pinnedData = &messageSpan.GetPinnableReference())
                {
                    // Message data.
                    //
                    IoVec ioVec = default;
                    ioVec.IovBase = new IntPtr(pinnedData);
                    ioVec.IovLength = (ulong)messageSpan.Length;

                    // #define SOL_SOCKET 1
                    ControlMessage<int> controlMessage = default;
                    controlMessage.Header.ControlMessageLength = (ulong)sizeof(ControlMessage<int>);
                    controlMessage.Header.ControlMessageLevel = 1;
                    controlMessage.Header.ControlMessageType = SocketLevelMessageType.ScmRights;
                    controlMessage.Value = 0;

                    // Construct the message.
                    //
                    MessageHeader message = default;

                    message.MessageName = IntPtr.Zero;
                    message.MessageNameLength = 0;

                    message.MessageIoVec = &ioVec;
                    message.MessageIoVecLength = 1;

                    message.MessageControl = &controlMessage.Header;
                    message.MessageControlLength = controlMessage.Header.ControlMessageLength;

                    ulong bytesRead = Native.ReceiveMessage(socket.Handle, ref message, 0);

                    if ((long)bytesRead == -1)
                    {
                        throw new SocketException(Marshal.GetLastWin32Error());
                    }

                    int messageSize = checked((int)bytesRead);

                    if (messageSize != 0)
                    {
                        if (message.MessageControlLength != 0)
                        {
                            fileDescriptor = new IntPtr(controlMessage.Value);
                        }

                        buffer = messageSpan.Slice(0, messageSize).ToArray();
                    }

                    return messageSize;
                }
            }
        }

        /// <summary>
        /// Sends the message and the file descriptor via Unix domain socket.
        /// </summary>
        /// <typeparam name="T">Type of the message.</typeparam>
        /// <param name="socket"></param>
        /// <param name="message"></param>
        /// <param name="fileDescriptor"></param>
        public static void SendMessageAndFileDescriptor<T>(
            this Socket socket,
            ref T message,
            IntPtr fileDescriptor)
            where T : struct
        {
            Span<T> messageSpan = MemoryMarshal.CreateSpan(ref message, 1);

            int sendBytes = SendMessageAndFileDescriptor(
                socket,
                MemoryMarshal.Cast<T, byte>(messageSpan),
                fileDescriptor);

            if (sendBytes != Marshal.SizeOf<T>())
            {
                throw new InvalidOperationException();
            }
        }

        private static int SendMessageAndFileDescriptor(
            this Socket socket,
            ReadOnlySpan<byte> messageData,
            IntPtr fileDescriptor)
        {
            if (socket == null)
            {
                throw new ArgumentNullException(nameof(socket));
            }

            if (fileDescriptor == null)
            {
                throw new ArgumentNullException(nameof(fileDescriptor));
            }

            unsafe
            {
                fixed (byte* pinnedData = &messageData.GetPinnableReference())
                {
                    // Message data.
                    //
                    IoVec ioVec = default;
                    ioVec.IovBase = new IntPtr(pinnedData);
                    ioVec.IovLength = (ulong)messageData.Length;

                    // Construct the message.
                    //
                    MessageHeader message = default;

                    message.MessageName = IntPtr.Zero;
                    message.MessageNameLength = 0;

                    message.MessageIoVec = &ioVec;
                    message.MessageIoVecLength = 1;

                    // Control message.
                    //
                    ControlMessage<int> controlMessage = default;
                    if (fileDescriptor != Native.InvalidPointer)
                    {
                        // #define SOL_SOCKET 1
                        controlMessage.Header.ControlMessageLength = (ulong)sizeof(ControlMessage<int>);
                        controlMessage.Header.ControlMessageLevel = 1;
                        controlMessage.Header.ControlMessageType = SocketLevelMessageType.ScmRights;
                        controlMessage.Value = fileDescriptor.ToInt32();

                        message.MessageControl = &controlMessage.Header;
                        message.MessageControlLength = controlMessage.Header.ControlMessageLength;
                    }

                    // Send the message.
                    //
                    ulong bytesSent = Native.SendMessage(socket.Handle, ref message, 0);

                    if ((long)bytesSent == -1)
                    {
                        throw new SocketException(Marshal.GetLastWin32Error());
                    }

                    int sent = checked((int)bytesSent);
                    return sent;
                }
            }
        }
    }
}
