//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: ExternalIntegrationExample.cpp
//
// Purpose:
//  This is a simple external C++ project main function file.
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#include "include/Common.h"

// Include platform specific implementations of some MLOS functions.
// Only needed in one compilation unit for a given target.
//
#include "MlosPlatform.Std.inl"

void ThrowIfFail(HRESULT hr)
{
    if (FAILED(hr))
    {
        throw std::exception();
    }
}

int main()
{
    // Create the MlosContext.
    //
    DefaultMlosContextFactory mlosContextFactory;
    HRESULT hr = mlosContextFactory.Create();
    ThrowIfFail(hr);

    Mlos::Core::MlosContext& mlosContext = mlosContextFactory.m_context;

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

    // Register the SettingsRegistry assembly with the external agent.
    //
    hr = mlosContext.RegisterSettingsAssembly(
        "ExternalIntegrationExample.SettingsRegistry.dll",
        ExternalIntegrationExample::ObjectDeserializationHandler::DispatchTableBaseIndex());
    ThrowIfFail(hr);

    // Create a component configuration object.
    // This will be stored in a shared memory region below for use by both the
    // component and the external agent.
    //
    Mlos::Core::ComponentConfig<ExternalIntegrationExample::SmartComponentExampleConfig> config(mlosContext);

    // Initialize the config with default values.
    //
    config.ActiveConfigId = 1;
    config.NewConfigId = 1;
    config.Size = 100;

    // Checks to see if there's already a shared memory region for storing the
    // config for this component and if not creates it.
    //
    hr = mlosContext.RegisterComponentConfig(config);
    ThrowIfFail(hr);

    // Pretend we did something with the component.

    // Place an example message onto the shared memory ring buffer.
    //
    ExternalIntegrationExample::SmartComponentExampleTelemetryMessage msg = { };
    msg.RequestKey = 42;
    msg.RequestType = ExternalIntegrationExample::ComponentRequestType::Put;
    msg.RequestSize = sizeof(msg.RequestKey);
    msg.RequestDuration = 7.0;
    msg.ResponseType = ExternalIntegrationExample::ComponentResponseType::Success;
    msg.Size = config.Size;

    mlosContext.SendTelemetryMessage(msg);

    // For now we aren't bothering to try and receive any message from an agent.

    std::cout << "Hello World!" << std::endl;

    // Terminate the feedback channel.
    //
    mlosContext.TerminateFeedbackChannel();

    // At this point there are no active feedback channel reader threads.
    // Now, terminate the control channel.
    //
    mlosContext.TerminateControlChannel();

    return 0;
}
