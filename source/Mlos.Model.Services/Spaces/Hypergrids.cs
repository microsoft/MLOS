// -----------------------------------------------------------------------
// <copyright file="Hypergrids.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Text.Json;
using System.Text.Json.Serialization;

using Mlos.Model.Services.Spaces.JsonConverters;

namespace Mlos.Model.Services.Spaces
{
    /// <summary>
    /// Hypergrid interace.
    /// </summary>
    public abstract class IHypergrid
    {
        public abstract string ToJson();
    }

    public class Hypergrid : IHypergrid
    {
        private static readonly JsonSerializerOptions JsonSerializerOptions = new JsonSerializerOptions
        {
            WriteIndented = true,
            Converters =
            {
                new JsonStringEnumConverter(),
                new HypergridJsonConverter(),
                new DimensionJsonConverter(),
                new SubgridJoinJsonConverter(),
                new HashSetJsonConverter<SubgridJoin>(),
                new JsonDictionaryConverter<string, HashSet<SubgridJoin>>(),
            },
        };

        /// <summary>
        /// Create Hypergrid from json string.
        /// </summary>
        /// <param name="jsonString"></param>
        /// <returns></returns>
        public static Hypergrid FromJson(string jsonString)
        {
            Hypergrid hypergrid = (jsonString != null) ? JsonSerializer.Deserialize<Hypergrid>(jsonString, JsonSerializerOptions) : null;

            return hypergrid;
        }

        /// <summary>
        /// Internal structure describing subgrid joins.
        /// </summary>
        internal struct SubgridJoin
        {
            internal IDimension OnExternalJoin { get; set; }

            internal Hypergrid Subgrid;
        }

        // This is for the benefit of the JsonSerializer.
        public enum HypergridType
        {
            SimpleHypergrid,
            CompositeHypergrid,
        }

        public string Name { get; set; }

        public HypergridType ObjectType { get; set; }

        public ReadOnlyCollection<IDimension> Dimensions { get; }

        public Hypergrid RootGrid { get; private set; }

        internal Dictionary<string, HashSet<SubgridJoin>> Subgrids { get; }

        public Hypergrid(string name, IDimension dimension)
        {
            ObjectType = HypergridType.SimpleHypergrid;
            Name = name;
            Dimensions = new ReadOnlyCollection<IDimension>(new[] { dimension });
            Subgrids = new Dictionary<string, HashSet<SubgridJoin>>();
        }

        public Hypergrid(string name, params IDimension[] dimensions)
        {
            ObjectType = HypergridType.SimpleHypergrid;
            Name = name;
            Dimensions = new ReadOnlyCollection<IDimension>(dimensions);
            Subgrids = new Dictionary<string, HashSet<SubgridJoin>>();
        }

        internal Hypergrid(string name, IDimension[] dimensions, Dictionary<string, HashSet<SubgridJoin>> subgrids)
        {
            ObjectType = HypergridType.SimpleHypergrid;
            Name = name;
            Dimensions = new ReadOnlyCollection<IDimension>(dimensions);
            Subgrids = subgrids;
        }

        /// <summary>
        /// Joins the subgrid on the specified dimension.
        /// </summary>
        /// <param name="subgrid"></param>
        /// <param name="onExternalDimension"></param>
        /// <returns></returns>
        public Hypergrid Join(Hypergrid subgrid, IDimension onExternalDimension)
        {
            if (!Subgrids.ContainsKey(onExternalDimension.Name))
            {
                Subgrids.Add(onExternalDimension.Name, new HashSet<SubgridJoin>());
            }

            Subgrids[onExternalDimension.Name].Add(
                new SubgridJoin
                {
                    Subgrid = subgrid,
                    OnExternalJoin = onExternalDimension,
                });

            subgrid.RootGrid = this;

            return this;
        }

        /// <inheritdoc/>
        public override string ToJson()
        {
            return JsonSerializer.Serialize(this, JsonSerializerOptions);
        }
    }
}
