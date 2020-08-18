// -----------------------------------------------------------------------
// <copyright file="ModelsDatabaseConnectionDetails.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Text.Json;

namespace Mlos.Model.Services.ModelsDb
{
    internal class ModelsDatabaseConnectionDetails
    {
        public static ModelsDatabaseConnectionDetails FromJsonFile(string path)
        {
            string connectionDetailsJsonString = File.ReadAllText(path);
            ModelsDatabaseConnectionDetails connectionDetails = JsonSerializer.Deserialize<ModelsDatabaseConnectionDetails>(connectionDetailsJsonString);
            return connectionDetails;
        }

        public string Host { get; set; }
        public string DatabaseName { get; set; }
        public string Username { get; set; }
        public string Password { get; set; }

        [DefaultValue(false)]
        public bool TrustedConnection { get; set; }

        [DefaultValue(60)]
        public int ConnectionTimeoutS { get; set; }

        public string ConnectionString
        {
            get
            {
                if (TrustedConnection)
                {
                    return @$"Data Source={Host}; Database={DatabaseName}; Trusted_Connection=True; Connection Timeout={ConnectionTimeoutS}";
                }
                else
                {
                    return @$"Data Source={Host}; Database={DatabaseName}; UID={Username}; PWD={Password}; Connection Timeout={ConnectionTimeoutS}";
                }
            }
        }
    }
}
