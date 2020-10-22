// -----------------------------------------------------------------------
// <copyright file="NamedSemaphore.Linux.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System.ComponentModel;
using System.IO;
using System.Runtime.InteropServices;

namespace Mlos.Core.Linux
{
    /// <summary>
    /// Named semaphore.
    /// </summary>
    public class NamedSemaphore : Mlos.Core.NamedEvent
    {
        /// <summary>
        /// Creates or opens a named semaphore.
        /// </summary>
        /// <param name="name"></param>
        /// <returns></returns>
        public static new NamedSemaphore CreateOrOpen(string name)
        {
            var namedSemaphore = new NamedSemaphore(name, Native.OpenFlags.O_CREAT);

            return namedSemaphore;
        }

        private NamedSemaphore(string name, Native.OpenFlags openFlags)
        {
            semaphoreHandle = Native.SemaphoreOpen(
                name,
                openFlags,
                Native.ModeFlags.S_IRUSR | Native.ModeFlags.S_IWUSR,
                0);

            if (semaphoreHandle.IsInvalid)
            {
                throw new IOException(
                    $"Failed to create a NamedSemaphore {name}",
                    innerException: new Win32Exception(Marshal.GetLastWin32Error()));
            }

            semaphoreName = name;
        }

        /// <inheritdoc/>
        public override bool Signal()
        {
            int result = Native.SemaphorePost(semaphoreHandle);

            return result == 0;
        }

        /// <inheritdoc/>
        public override bool Wait()
        {
            int result = Native.SemaphoreWait(semaphoreHandle);

            return result == 0;
        }

        /// <summary>
        /// Protected implementation of Dispose pattern.
        /// </summary>
        /// <param name="disposing"></param>
        protected override void Dispose(bool disposing)
        {
            if (isDisposed || !disposing)
            {
                return;
            }

            semaphoreHandle?.Dispose();

            if (CleanupOnClose)
            {
                // Unlink semaphore. Ignore the errors.
                //
                if (semaphoreName != null)
                {
                    _ = Native.SemaphoreUnlink(semaphoreName);
                }

                CleanupOnClose = false;
            }

            isDisposed = true;
        }

        private readonly SemaphoreSafeHandle semaphoreHandle;

        private readonly string semaphoreName;
    }
}
