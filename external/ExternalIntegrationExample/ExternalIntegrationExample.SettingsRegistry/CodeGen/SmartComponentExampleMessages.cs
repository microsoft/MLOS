// -----------------------------------------------------------------------
// <copyright file="SmartComponentExampleMessages.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using Mlos.SettingsSystem.Attributes;
using Mlos.SettingsSystem.StdTypes;

namespace ExternalIntegrationExample
{
    /// <summary>
    /// An enum describing the request type for this component.
    /// </summary>
    public enum ComponentRequestType
    {
        /// <summary>
        /// A Get request type.
        /// </summary>
        Get,

        /// <summary>
        /// A Put request type.
        /// </summary>
        Put,

        /// <summary>
        /// A Delete request type.
        /// </summary>
        Delete,
    }

    /// <summary>
    /// An enum describing the response type for the request.
    /// </summary>
    public enum ComponentResponseType
    {
        /// <summary>
        /// A Success response type.
        /// </summary>
        Success,

        /// <summary>
        /// A Failure response type.
        /// </summary>
        Failure,
    }

    /// <summary>
    /// A message to ask optimizer for the new configuration.
    /// </summary>
    /// <remarks>
    /// Note: This message contains no members to detail the request.
    /// It's very existence on the channel is signal enough of its intent.
    /// </remarks>
    [CodegenMessage]
    public partial struct RequestConfigUpdateExampleMessage
    {
    }

    /// <summary>
    /// A telemetry message to inform the agent of the smart component's activity/state.
    /// </summary>
    /// <remarks>
    /// Messages can be combined/aggregated by the agent in various ways before being passed to the optimizer.
    /// </remarks>
    [CodegenMessage]
    public partial struct SmartComponentExampleTelemetryMessage
    {
        /// <summary>
        /// The key for the Request.
        /// </summary>
        [ScalarSetting]
        internal long RequestKey;

        /// <summary>
        /// What type of request it was.
        /// </summary>
        [ScalarSetting]
        internal ComponentRequestType RequestType;

        /// <summary>
        /// The size of the request (or response in the case of Get).
        /// </summary>
        [ScalarSetting]
        internal long RequestSize;

        /// <summary>
        /// The duration of the request.
        /// </summary>
        [ScalarSetting]
        internal double RequestDuration;

        /// <summary>
        /// The status of the response.
        /// </summary>
        [ScalarSetting]
        internal ComponentResponseType ResponseType;

        /// <summary>
        /// The size of the component.
        /// </summary>
        [ScalarSetting]
        internal long Size;
    }
}
