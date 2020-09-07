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
    /// Holds all intelligence. This is a proxy with a cache to the MLOS model service.
    /// </summary>
    public static class MlosAgentServer
    {
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

        public static void Main(string[] args)
        {
            // TODO: use some proper arg parser. For now let's keep it simple.
            //
            string executableFilePath = null;
            string modelsDatabaseConnectionDetailsFile = null;

            foreach (string arg in args)
            {
                if (Path.GetExtension(arg) == ".exe")
                {
                    executableFilePath = arg;
                }
                else if (Path.GetExtension(arg) == ".json")
                {
                    modelsDatabaseConnectionDetailsFile = arg;
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

                Uri optimizerAddressUri = new Uri("http://localhost:50051");
                MlosContext.OptimizerFactory = new MlosOptimizer.BayesianOptimizerFactory(optimizerAddressUri);
            }

            // Create circular buffer shared memory before running the target process.
            //
            MainAgent.InitializeSharedChannel();

            // Active learning, almost done. In active learning the MlosAgentServer controls the workload against the target component.
            //
            if (executableFilePath != null)
            {
                targetProcessManager = new TargetProcessManager(executableFilePath: executableFilePath);
                targetProcessManager.StartTargetProcess();
            }

            var cancelationTokenSource = new CancellationTokenSource();

            Task grpcServerTask = CreateHostBuilder(Array.Empty<string>()).Build().RunAsync(cancelationTokenSource.Token);

            Console.WriteLine("Starting Mlos.Agent");
            Task mlosAgentTask = Task.Factory.StartNew(
                () => MainAgent.RunAgent(),
                TaskCreationOptions.LongRunning);

            if (targetProcessManager != null)
            {
                targetProcessManager.WaitForTargetProcessToExit();
                targetProcessManager.Dispose();
                MainAgent.UninitializeSharedChannel();
            }

            Console.WriteLine("Waiting for Mlos.Agent to exit");

            mlosAgentTask.Wait();
            mlosAgentTask.Dispose();

            cancelationTokenSource.Cancel();
            grpcServerTask.Wait();

            grpcServerTask.Dispose();
            cancelationTokenSource.Dispose();

            Console.WriteLine("Mlos.Agent exited.");
        }
    }
}
