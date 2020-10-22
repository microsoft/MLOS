//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: Main.cpp
//
// Purpose:
//  The main entrypoint to the SmartCache example.
//
//  It's meant as an end-to-end microbenchmark example for the C++ version of the
//  SmartCache Python Notebook example.
//
//  It provides different cache replacement policies and cache sizes as tunables
//  for an optimizer to tune for different workloads.
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

// Include all the common headers for the application
// (including Mlos.Core and component settings registry code generation output)
//
#include "stdafx.h"

// Include platform specific implementations of some MLOS functions.
// Only needed in one compilation unit for a given target.
//
#include "MlosPlatform.Std.inl"

using namespace Mlos::Core;
using namespace SmartCache;

#include "SmartCacheImpl.h"
#include "Workloads.h"

// A basic result code handler.
//
// MLOS is cross-platform, but started in Windows, so many of the return values
// reflect that.
//
// HRESULTs are an error code encoding mechanism typically used in Windows environments.
// See Also: https://en.wikipedia.org/wiki/HRESULT
//
void ThrowIfFail(HRESULT hr)
{
    if (FAILED(hr))
    {
        throw std::exception();
    }
}

int
__cdecl
main(
    _In_ int argc,
    _In_ char* argv[])
{
    UNUSED(argc);
    UNUSED(argv);

    // Create the MlosContext.
    // It encapsulates all of the shared memory regions for this component.
    // In this case we use an interprocess implementation to communicate with an
    // external agent.
    // There are 3 (unidirectional) channels setup:
    // 1. Control: for registering components and memory for their configs in
    // the global region
    // 2. Telemetry: for sending messages from/about the application component
    // to the agent (e.g. performance metrics)
    // 3. Feedback: for receiving messages from the agent (e.g. configuration
    // updates)
    //
    Mlos::Core::InterProcessMlosContextInitializer mlosContextInitializer;
    HRESULT hr = mlosContextInitializer.Initialize();
    ThrowIfFail(hr);

    Mlos::Core::InterProcessMlosContext mlosContext(std::move(mlosContextInitializer));

    // Create a feedback channel receiver thread.
    //
    ISharedChannel& feedbackChannel = mlosContext.FeedbackChannel();

    // This background thread uses a lambda to monitor the feedback channel for
    // new messages and process them using the callbacks registered for each
    // message type in the global dispatch table.
    //
    std::future<bool> feedbackChannelReader = std::async(
        std::launch::async,
        [&feedbackChannel]
    {
        // GlobalDispatchTable defines the set of recognized messages by this
        // application.
        // See GlobalDispatchTable.h for details.
        //
        auto globalDispatchTable = GlobalDispatchTable();

        // This starts a loop to handle reading messages from the feedback
        // channel, looking them up in the dispatch table, and calling the
        // callbacks associated with them.
        //
        feedbackChannel.ProcessMessages(globalDispatchTable.data(), globalDispatchTable.size());

        return true;
    });

    // Register the SmartCache.SettingsRegistry assembly with the external agent.
    //
    // This prepares the external agent to begin handling messages from our
    // smart component on new telemetry and feedback channels.
    //
    // To do that it sends a RegisterAssemblyRequestMessage to the agent on the
    // control channel that includes the name of settings registry (annotated C#
    // data structures used for code generation) assembly (dll) for this smart
    // component.
    //
    // When the (C#) agent receives that message it dynamically loads the
    // specified dll into its address space and calls an AssemblyInitializer
    // static class within that dll to setup the message handlers (callbacks).
    //
    // See Also: SmartCache.SettingsRegistry/AssemblyInitializer.cs
    //
    hr = mlosContext.RegisterSettingsAssembly(
        "SmartCache.SettingsRegistry.dll",
        SmartCache::ObjectDeserializationHandler::DispatchTableBaseIndex());
    ThrowIfFail(hr);

    // Create a component configuration object.
    // This will be stored in a shared memory region below for use by both the
    // component and the external agent.
    //
    Mlos::Core::ComponentConfig<SmartCache::SmartCacheConfig> config(mlosContext);

    // Initialize config with default values.
    //
    // TODO: Eventually we expect these default values to be initialized from
    // the SettingsRegistry code generation process themselves.
    //
    config.ConfigId = 1;
    config.EvictionPolicy = SmartCache::CacheEvictionPolicy::LeastRecentlyUsed;
    config.CacheSize = 100;

    // Checks to see if there's already a shared memory region for storing the
    // config for this component and if not creates it.
    //
    hr = mlosContext.RegisterComponentConfig(config);
    ThrowIfFail(hr);

    // Create an instance of our SmartCache component to tune.
    //
    // Note that we pass it a ComponentConfig instance, which also includes our
    // MlosContext instance, so that the component can internally send telemetry
    // messages and update its config from the component specific shared memory
    // region.
    //
    SmartCacheImpl<int32_t, int32_t> smartCache(config);

    // Now we run a workload to exercise the SmartCache.
    //
    for (int observations = 0; observations < 100; observations++)
    {
        std::cout << "observations: " << observations << std::endl;

        for (int i = 0; i < 20; i++)
        {
            CyclicalWorkload(2048, smartCache);
        }

        // After having run a workload for a while, we want to check for a new
        // config suggestion from an optimizer.
        // In this case we make it a blocking call.

        // First, create some condition variables to help signal when the new
        // config is ready to be consumed.
        //
        bool isConfigReady = false;
        std::mutex waitForConfigMutex;
        std::condition_variable waitForConfigCondVar;

        // Also, setup a callback lambda function for handling the
        // SharedConfigUpdatedFeedbackMessage we expect to receive from the
        // agent after we request a config update with a RequestNewConfigurationMessage.
        //
        // Note: this lambda will be invoked by the background task setup above
        // for processing messages on the feedback channel.
        //
        ObjectDeserializationCallback::Mlos::Core::SharedConfigUpdatedFeedbackMessage_Callback =
            [&waitForConfigMutex, &waitForConfigCondVar,
             &isConfigReady](Proxy::Mlos::Core::SharedConfigUpdatedFeedbackMessage&& msg)
            {
                // The contents of the message are irrelevant in this case.
                // It's just a signal that the RequestNewConfigurationMessage
                // has been processed by the agent.
                //
                UNUSED(msg);

                // So, we will just notify the waiting loop (below) that the
                // message has been processed now and is ready to be read.
                //
                std::unique_lock<std::mutex> lock(waitForConfigMutex);
                isConfigReady = true;
                waitForConfigCondVar.notify_all();
            };

        // Send a request to obtain a new configuration from the optimizer.
        //
        // Note: the message (as defined in
        // SmartCache.SettingsRegistry/CodeGen/SmartCache.cs) has no members, so
        // there's no details to fill in here (and it is just zero-initialized).
        // It's simply a signal to send to the external agent to request a new
        // config be populated in the shared memory region.
        //
        SmartCache::RequestNewConfigurationMessage msg = { 0 };
        mlosContext.SendTelemetryMessage(msg);

        // Now, we wait for the external agent to respond to our request.
        // When it does, the message will be handled by the callback lambda we
        // setup above which will signal the lock and conditional variables.
        //
        // To see how the external agent will process the request, see the
        // RequestNewConfigurationMessage handler in
        // SmartCache.SettingsRegistry/AssemblyInitializer.cs.
        //
        std::unique_lock<std::mutex> lock(waitForConfigMutex);
        while (!isConfigReady)
        {
            std::cout << "Waiting for agent to respond with a new configuration." << std::endl;
            waitForConfigCondVar.wait(lock);
        }

        // Now, there is a new config setup in the shared memory region.
        // We first make a copy of it (to prevent torn reads).
        //
        config.Update();

        // Next, we instruct our component to reconfigure itself before
        // exploring more samples in the configuration space.
        //
        smartCache.Reconfigure();
    }

    // Terminate the feedback channel.
    //
    mlosContext.TerminateFeedbackChannel();

    // At this point there are no active feedback channel reader threads.
    // Now, terminate the control channel.
    //
    mlosContext.TerminateControlChannel();

    feedbackChannelReader.wait();
}
