// -----------------------------------------------------------------------
// <copyright file="TargetProcessManager.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text;

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

        public TargetProcessManager(string executableFilePath)
        {
            this.executableFilePath = executableFilePath;
            targetProcess = null;
        }

        ~TargetProcessManager()
        {
            Dispose(false);
        }

        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }

        private void Dispose(bool isManualDisposing)
        {
            if (targetProcess != null)
            {
                // TODO: what happens if the process is still running when we call Dispose? Should we WaitForExit first? Should we kill?
                //
                targetProcess.Dispose();
            }
        }

        public void StartTargetProcess()
        {
            targetProcess = new Process
            {
                StartInfo = new ProcessStartInfo
                {
                    FileName = executableFilePath,
                    RedirectStandardOutput = true,
                    UseShellExecute = false,
                },
            };

            targetProcess.OutputDataReceived += (sendingProcess, outLine) => Console.WriteLine(outLine.Data);
            targetProcess.ErrorDataReceived += (sendingProcess, outLine) => Console.WriteLine(outLine.Data);

            targetProcess.Start();

            targetProcess.BeginOutputReadLine();
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

                targetProcess.Dispose();
                targetProcess = null;
            }
        }
    }
}
