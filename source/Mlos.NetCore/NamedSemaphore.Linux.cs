// -----------------------------------------------------------------------
// <copyright file="NamedSemaphore.Linux.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System.Threading;

namespace Mlos.Core.Linux
{
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
            if (disposed)
            {
                return;
            }

            if (disposing)
            {
                semaphoreHandle?.Dispose();
            }

            disposed = true;
        }

        private readonly SemaphoreSafeHandle semaphoreHandle;
    }
}