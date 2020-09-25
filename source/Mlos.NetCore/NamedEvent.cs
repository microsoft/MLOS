// -----------------------------------------------------------------------
// <copyright file="NamedEvent.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Runtime.ConstrainedExecution;
using System.Runtime.InteropServices;

namespace Mlos.Core
{
    /// <summary>
    /// An abstract class representing a named event.
    /// </summary>
    public abstract class NamedEvent : CriticalFinalizerObject, IDisposable
    {
        /// <summary>
        /// Creates or opens a named event.
        /// </summary>
        /// <param name="name"></param>
        /// <returns></returns>
        public static NamedEvent CreateOrOpen(string name)
        {
            if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
            {
                return Windows.NamedEvent.CreateOrOpen(name);
            }
            else if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
            {
                return Linux.NamedSemaphore.CreateOrOpen(name);
            }
            else
            {
                throw new InvalidOperationException("Unsupported OS.");
            }
        }

        /// <summary>
        /// Finalizes an instance of the <see cref="NamedEvent"/> class.
        /// </summary>
        ~NamedEvent()
        {
            Dispose(false);
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

        /// <summary>
        /// Sets the state of the event to signaled, allowing one or more waiting threads to proceed.
        /// </summary>
        /// <returns></returns>
        public abstract bool Signal();

        /// <summary>
        /// Blocks the current thread until the current eventWaitHandle receives a signal.
        /// </summary>
        /// <returns></returns>
        public abstract bool Wait();

        /// <summary>
        /// Protected implementation of Dispose pattern.
        /// </summary>
        /// <param name="disposing"></param>
        protected abstract void Dispose(bool disposing);

        /// <summary>
        /// True if object has been disposed.
        /// </summary>
        protected bool isDisposed = false;

        /// <summary>
        /// Indicates if we should cleanup OS resources when closing the shared memory map view.
        /// </summary>
        /// <returns></returns>
        public bool CleanupOnClose;
    }
}
