// -----------------------------------------------------------------------
// <copyright file="RemoteProcedureCall.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Text;

namespace Mlos.Model.Services.ModelsDb.ObjectRelationalMappings
{
    public class RemoteProcedureCall
    {
        private static readonly Dictionary<string, RPCStatus> StatusStringMappings = new Dictionary<string, RPCStatus>()
        {
            // These names have to match the names in the Models Database schema.
            //
            { "submitted", RPCStatus.Submitted },
            { "in progress", RPCStatus.InProgress },
            { "complete", RPCStatus.Complete },
            { "failed", RPCStatus.Failed },
            { "cancelled", RPCStatus.Cancelled },
            { "aborted", RPCStatus.Aborted },
            { "timed out", RPCStatus.TimedOut },
        };

        public enum RPCStatus
        {
            None,
            Submitted,
            InProgress,
            Complete,
            Failed,
            Cancelled,
            Aborted,
            TimedOut,
        }

        public Guid? RequestId { get; set; }

        public DateTime? RequestSubmissionTime { get; set; }

        public RPCStatus Status { get; set; }

        public RPCStatus ExpectedCurrentStatus { get; set; }

        public string RemoteProcedureName { get; set; }
        public string ExecutionContextJsonString { get; set; }
        public string ArgumentsJsonString { get; set; }
        public string ResultJsonString { get; set; }
        public TimeSpan? TimeoutDuration { get; set; }
        public DateTime? Timeout { get; set; }

        public RemoteProcedureCall(
            string remoteProcedureName,
            string executionContextJsonString,
            string argumentsJsonString,
            TimeSpan? timeoutDuration = null)
        {
            Status = RPCStatus.None;
            ExpectedCurrentStatus = RPCStatus.None;
            RemoteProcedureName = remoteProcedureName;
            ExecutionContextJsonString = executionContextJsonString;
            ArgumentsJsonString = argumentsJsonString;
            TimeoutDuration = timeoutDuration;
        }

        public void SetStatus(string statusString)
        {
            Status = StatusStringMappings[statusString];
        }
    }
}
