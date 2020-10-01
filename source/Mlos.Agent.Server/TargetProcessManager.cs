// -----------------------------------------------------------------------
// <copyright file="TargetProcessManager.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Diagnostics;

namespace Mlos.Agent.Server
{
    /// <summary>
    /// Under some circumstances (notably in the case of unit tests and active
    /// learning) we want the Mlos.Agent.Server to control the target process.
    ///
    /// TargetProcessManager takes care of starting the process and disposing of it.
    /// </summary>
    internal class TargetProcessManager : IDisposable
    {
        private readonly string executableFilePath;

        private Process targetProcess;

        private bool isDisposed;

        public TargetProcessManager(string executableFilePath)
        {
            this.executableFilePath = executableFilePath;
            targetProcess = null;
        }

        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }

        private void Dispose(bool disposing)
        {
            if (isDisposed || !disposing)
            {
                return;
            }

            targetProcess?.Dispose();
            targetProcess = null;

            isDisposed = true;
        }

        public void StartTargetProcess()
        {
            targetProcess = new Process
            {
                StartInfo = new ProcessStartInfo
                {
                    FileName = executableFilePath,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                },
            };

            targetProcess.OutputDataReceived += (sendingProcess, outLine) =>
            {
                Console.Out.WriteLine(outLine.Data);
                Console.Out.Flush();
            };
            targetProcess.ErrorDataReceived += (sendingProcess, outLine) => Console.Error.WriteLine(outLine.Data);

            targetProcess.Start();

            targetProcess.BeginOutputReadLine();
            targetProcess.BeginErrorReadLine();
        }

        public void WaitForTargetProcessToExit()
        {
            if (targetProcess != null)
            {
                targetProcess.WaitForExit();

                // Check the error code, if target returns non-zero code, throw an exception to crash the agent.
                // This has the effect of making the tests fail when the target process exits abnormally.
                //
                if (targetProcess.ExitCode != 0)
                {
                    throw new ApplicationException($"Target application exited with error code:{targetProcess.ExitCode}");
                }
            }
        }

        /// <summary>
        /// Terminate target process.
        /// </summary>
        /// <remarks>
        /// Mlos.Agent.Service calls this method on shutdown if the target process is still active.
        /// </remarks>
        public void TerminateTargetProcess()
        {
            if (targetProcess != null)
            {
                try
                {
                    targetProcess.Kill();
                }
                catch
                {
                    if (!targetProcess.HasExited)
                    {
                        // If the process is still active, rethrow the exception.
                        //
                        throw;
                    }
                }
            }
        }
    }
}
