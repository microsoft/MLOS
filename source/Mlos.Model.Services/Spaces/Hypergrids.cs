// -----------------------------------------------------------------------
// <copyright file="Hypergrids.cs" company="Microsoft Corporation">
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

using Mlos.Model.Services.Spaces.JsonConverters;

namespace Mlos.Model.Services.Spaces
{
    /// <summary>
    /// Base class for SimpleHypergrid and CompositeHypergrid.
    ///
    /// This is just the first step in the implementation. As the need arises we will bring
    /// the C# implementation of Hypergrids to par with the Python implementation.
    /// </summary>
    public abstract class Hypergrid
    {
        public abstract string ToJson();
    }

    public class SimpleHypergrid : Hypergrid
    {
        // This is for the benefit of the JsonSerializer.
        public enum HypergridType
        {
            SimpleHypergrid,
            CompositeHypergrid,
        }

        public HypergridType ObjectType { get; set; }
        public string Name { get; set; }
        public List<IDimension> Dimensions { get; }

        public SimpleHypergrid(string name, List<IDimension> dimensions)
        {
            ObjectType = HypergridType.SimpleHypergrid;
            Name = name;
            Dimensions = dimensions;
        }

        public override string ToJson()
        {
            JsonSerializerOptions jsonSerializerOptions = new JsonSerializerOptions
            {
                WriteIndented = true,
                Converters =
                {
                    new SimpleHypergridJsonConverter(),
                    new DimensionJsonConverter(),
                    new JsonStringEnumConverter(),
                },
            };

            return JsonSerializer.Serialize(this, jsonSerializerOptions);
        }
    }

    public abstract class CompositeHypergrid : Hypergrid
    {
    }
}
