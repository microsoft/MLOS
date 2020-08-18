// -----------------------------------------------------------------------
// <copyright file="SimpleBayesianOptimizerConfig.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Mlos.Model.Services.Client.Proxies
{
    public class SimpleBayesianOptimizerConfig
    {
        [JsonPropertyName("utility_function")]
        public string UtilityFunction { get; set; }

        [JsonPropertyName("kappa")]
        public double Kappa { get; set; }

        [JsonPropertyName("xi")]
        public double Xi { get; set; }

        [JsonPropertyName("minimize")]
        public bool Minimize { get; set; }

        public string ToJson()
        {
            var jsonSerializerOptions = new JsonSerializerOptions
            {
                WriteIndented = true,
            };

            jsonSerializerOptions.Converters.Add(new JsonStringEnumConverter());
            return ToJson(jsonSerializerOptions);
        }

        public string ToJson(JsonSerializerOptions jsonSerializerOptions)
        {
            return JsonSerializer.Serialize(this, jsonSerializerOptions);
        }
    }
}
