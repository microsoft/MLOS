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
    }

    /// <summary>
    /// Structure describing joined subgrids.
    /// </summary>
    public struct JoinedSubgrid
    {
        public IDimension OnExternalJoin { get; set; }

        public Hypergrid Subgrid;
    }

    public class Hypergrid : IHypergrid
    {
        public enum HypergridType
        {
            /// <summary>
            /// Simple hypergrid.
            /// </summary>
            SimpleHypergrid,
        }

        public string Name { get; set; }

        public HypergridType ObjectType { get; set; }

        public ReadOnlyCollection<IDimension> Dimensions { get; }

        public Hypergrid RootGrid { get; private set; }

        public Dictionary<string, HashSet<JoinedSubgrid>> Subgrids { get; }

        public Hypergrid(string name, IDimension dimension)
        {
            ObjectType = HypergridType.SimpleHypergrid;
            Name = name;
            Dimensions = new ReadOnlyCollection<IDimension>(new[] { dimension });
            Subgrids = new Dictionary<string, HashSet<JoinedSubgrid>>();
        }

        public Hypergrid(string name, params IDimension[] dimensions)
        {
            ObjectType = HypergridType.SimpleHypergrid;
            Name = name;
            Dimensions = new ReadOnlyCollection<IDimension>(dimensions);
            Subgrids = new Dictionary<string, HashSet<JoinedSubgrid>>();
        }

        internal Hypergrid(string name, IDimension[] dimensions, Dictionary<string, HashSet<JoinedSubgrid>> subgrids)
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
                Subgrids.Add(onExternalDimension.Name, new HashSet<JoinedSubgrid>());
            }

            Subgrids[onExternalDimension.Name].Add(
                new JoinedSubgrid
                {
                    Subgrid = subgrid,
                    OnExternalJoin = onExternalDimension,
                });

            subgrid.RootGrid = this;

            return this;
        }
    }
}
