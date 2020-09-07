//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: Main.cpp
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#include "stdafx.h"

#include "MlosPlatform.Std.inl"

using namespace Mlos::Core;
using namespace SmartCache;

// Include codegen files.
//
#include "GlobalDispatchTable.h"

#include "SmartCacheImpl.h"
#include "Workloads.h"

void CheckHR(HRESULT hr)
{
    if (FAILED(hr))
    {
        throw std::exception();
    }
}

int
__cdecl
main(
    __in int argc,
    __in char* argv[])
{
    UNUSED(argc);
    UNUSED(argv);

    // Create MlosContext.
    //
    Mlos::Core::InterProcessMlosContextInitializer mlosContextInitializer;
    HRESULT hr = mlosContextInitializer.Initialize();
    CheckHR(hr);

    Mlos::Core::InterProcessMlosContext mlosContext(std::move(mlosContextInitializer));

    // Create a feedback channel receiver thread.
    //
    ISharedChannel& feedbackChannel = mlosContext.FeedbackChannel();

    std::future<bool> feedbackChannelReader = std::async(
        std::launch::async,
        [&feedbackChannel]
    {
        auto globalDispatchTable = GlobalDispatchTable();
        feedbackChannel.ReaderThreadLoop(globalDispatchTable.data(), globalDispatchTable.size());

        return true;
    });

    // Register Mlos.SmartCache Settings assembly.
    //
    hr = mlosContext.RegisterSettingsAssembly(
        "SmartCache.SettingsRegistry.dll",
        SmartCache::ObjectDeserializationHandler::DispatchTableBaseIndex());
    CheckHR(hr);

    // Create shared component configuration.
    //
    Mlos::Core::ComponentConfig<SmartCache::SmartCacheConfig> config(mlosContext);

    // Initialize config with default values.
    //
    config.ConfigId = 1;
    config.EvictionPolicy = SmartCache::CacheEvictionPolicy::LeastRecentlyUsed;
    config.CacheSize = 100;

    hr = mlosContext.RegisterComponentConfig(config);
    CheckHR(hr);

    // Create an intelligent component.
    //
    SmartCacheImpl<int32_t, int32_t> smartCache(config);

    for (int observations = 0; observations < 500; observations++)
    {
        for (int i = 0; i < 20; i++)
        {
            CyclicalWorkload(2048, smartCache);
        }

        bool isConfigReady = false;
        std::mutex waitForConfigMutex;
        std::condition_variable waitForConfigCondVar;

        // Setup a callback.
        //
        ObjectDeserializationCallback::Mlos::Core::SharedConfigUpdatedFeedbackMessage_Callback =
            [&waitForConfigMutex, &waitForConfigCondVar,
             &isConfigReady](Proxy::Mlos::Core::SharedConfigUpdatedFeedbackMessage&& msg)
            {
                // Ignore the message.
                //
                UNUSED(msg);

                std::unique_lock<std::mutex> lck(waitForConfigMutex);
                isConfigReady = true;
                waitForConfigCondVar.notify_all();
            };

        // Send a request to obtain a new configuration.
        //
        SmartCache::RequestNewConfigurationMesage msg = { 0 };
        mlosContext.SendTelemetryMessage(msg);

        std::unique_lock<std::mutex> lock(waitForConfigMutex);
        while (!isConfigReady)
        {
            waitForConfigCondVar.wait(lock);
        }

        config.Update();
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
