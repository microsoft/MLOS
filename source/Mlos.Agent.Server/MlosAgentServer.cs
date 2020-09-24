// -----------------------------------------------------------------------
// <copyright file="MlosAgentServer.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;

using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Server.Kestrel.Core;
using Microsoft.Extensions.Hosting;

using Mlos.Core;

using MlosOptimizer = Mlos.Model.Services.Client.BayesianOptimizer;

namespace Mlos.Agent.Server
{
    /// <summary>
    /// The MlosAgentServer acts as a simple external agent and shim helper to
    /// wrap the various communication channels (shared memory to/from the smart
    /// component, grpc to the optimizer, grpc from the notebooks).
    /// </summary>
    public static class MlosAgentServer
    {
        /// <summary>
        /// Starts a grpc server listening for requests from the notebook to drive
        /// the agent interactively.
        /// </summary>
        /// <param name="args">unused.</param>
        /// <returns>grpc server task.</returns>
        public static IHostBuilder CreateHostBuilder(string[] args) =>
            Host.CreateDefaultBuilder(args)
                .ConfigureWebHostDefaults(webBuilder =>
                {
                    webBuilder.ConfigureKestrel(options =>
                    {
                        // Setup a HTTP/2 endpoint without TLS.
                        //
                        options.ListenLocalhost(5000, o => o.Protocols = HttpProtocols.Http2);
                    });
                    webBuilder.UseStartup<GrpcServer.Startup>();
                });

        /// <summary>
        /// The main external agent server.
        /// </summary>
        /// <param name="args">command line arguments.</param>
        public static void Main(string[] args)
        {
            // TODO: use some proper arg parser. For now let's keep it simple.
            //
            string executableFilePath = null;
            string modelsDatabaseConnectionDetailsFile = null;

            foreach (string arg in args)
            {
                if (Path.GetExtension(arg) == ".json")
                {
                    modelsDatabaseConnectionDetailsFile = arg;
                }
                else
                {
                    // Linux executables don't have a suffix by default.
                    // So, for now just assume that anything else is an executable.
                    //
                    executableFilePath = arg;
                }
            }

            Console.WriteLine("Mlos.Agent.Server");
            TargetProcessManager targetProcessManager = null;

            // #TODO connect to gRpc optimizer only if user provided json file in the command line argument.
            // #TODO, make address configurable.
            //
            if (modelsDatabaseConnectionDetailsFile != null)
            {
                Console.WriteLine("Connected to Mlos.Optimizer");

                // This switch must be set before creating the GrpcChannel/HttpClient.
                //
                AppContext.SetSwitch("System.Net.Http.SocketsHttpHandler.Http2UnencryptedSupport", true);

                // This populates a variable for the various settings registry
                // callback handlers to use (by means of their individual
                // AssemblyInitializers) to know how they can connect with the
                // optimizer.
                //
                // See Also: AssemblyInitializer.cs within the SettingsRegistry
                // assembly project in question.
                //
                Uri optimizerAddressUri = new Uri("http://localhost:50051");
                MlosContext.OptimizerFactory = new MlosOptimizer.BayesianOptimizerFactory(optimizerAddressUri);
            }

            // Create (or open) the circular buffer shared memory before running the target process.
            //
            MainAgent.InitializeSharedChannel();

            // Active learning mode.
            //
            // TODO: In active learning mode the MlosAgentServer can control the
            // workload against the target component.
            //
            if (executableFilePath != null)
            {
                Console.WriteLine($"Starting {executableFilePath}");
                targetProcessManager = new TargetProcessManager(executableFilePath: executableFilePath);
                targetProcessManager.StartTargetProcess();
            }
            else
            {
                Console.WriteLine("No executable given to launch.  Will wait for agent to connect independently.");
            }

            var cancellationTokenSource = new CancellationTokenSource();

            Task grpcServerTask = CreateHostBuilder(Array.Empty<string>()).Build().RunAsync(cancellationTokenSource.Token);

            // Start the MainAgent message processing loop as a background thread.
            //
            // In MainAgent.RunAgent we loop on the shared memory control and
            // telemetry channels looking for messages and dispatching them to

            // their registered callback handlers.
            //
            // The set of recognized messages is dynamically registered using

            // the RegisterSettingsAssembly method which is called through the
            // handler for the RegisterAssemblyRequestMessage.
            //
            // Once registered, the SettingsAssemblyManager uses reflection to

            // search for an AssemblyInitializer inside those assemblies and
            // executes it in order to setup the message handler callbacks
            // within the agent.
            //
            // See Also: AssemblyInitializer.cs within the SettingsRegistry
            // assembly project in question.
            //
            Console.WriteLine("Starting Mlos.Agent");
            Task mlosAgentTask = Task.Factory.StartNew(
                MainAgent.RunAgent,
                TaskCreationOptions.LongRunning);

            if (targetProcessManager != null)
            {
                targetProcessManager.WaitForTargetProcessToExit();
                targetProcessManager.Dispose();
                MainAgent.UninitializeSharedChannel();
            }

            Console.WriteLine("Waiting for Mlos.Agent to exit");

            // Perform some cleanup.
            //
            mlosAgentTask.Wait();
            mlosAgentTask.Dispose();

            cancellationTokenSource.Cancel();
            grpcServerTask.Wait();

            grpcServerTask.Dispose();
            cancellationTokenSource.Dispose();

            Console.WriteLine("Mlos.Agent exited.");
        }
    }
}
