// -----------------------------------------------------------------------
// <copyright file="SemaphoreTests.Linux.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Threading;

using Mlos.Core.Linux;

using Xunit;

namespace Mlos.NetCore.UnitTest.Linux
{
    public class SemaphoreTests
    {
        /// <summary>
        /// Verifies if semaphore will correctly wait for the post signal.
        /// </summary>
        [Fact(Timeout = 5000)]
        public void VerifySemaphoreWaitAndPost()
        {
            const string semName = "/test";

            SemaphoreSafeHandle sem = Native.SemaphoreOpen(semName, Native.OpenFlags.O_CREAT, Native.ModeFlags.S_IRUSR | Native.ModeFlags.S_IWUSR, 0);

            var thread = new Thread(() =>
            {
                const string semName2 = "test";
                SemaphoreSafeHandle sem2 = Native.SemaphoreOpen(semName2, Native.OpenFlags.O_CREAT);

                Console.WriteLine("Waiting 1");
                int result_wait1 = Native.SemaphoreWait(sem2);
                Console.WriteLine("Done 1");

                Console.WriteLine("Waiting 2");
                int result_wait2 = Native.SemaphoreWait(sem2);
                Console.WriteLine("Done 2");

                sem2.Dispose();
            });
            thread.Start();

            Thread.Sleep(TimeSpan.FromSeconds(1));

            Console.WriteLine("sem_post 1");
            int result2 = Native.SemaphorePost(sem);
            sem.Dispose();

            // Reopen the semaphore.
            //
            sem = Native.SemaphoreOpen(semName, Native.OpenFlags.O_CREAT);
            Thread.Sleep(TimeSpan.FromSeconds(1));
            Console.WriteLine("sem_post 2");
            int result3 = Native.SemaphorePost(sem);

            thread.Join();

            sem.Dispose();

            // Unlink the semaphore, the semaphore is destroyed after the test process exits.
            //
            _ = Native.SemaphoreUnlink(semName);
        }
    }
}
