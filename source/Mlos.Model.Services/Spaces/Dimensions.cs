// -----------------------------------------------------------------------
// <copyright file="Dimensions.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text;

namespace Mlos.Model.Services.Spaces
{
    public enum DimensionTypeName
    {
        EmptyDimension,
        ContinuousDimension,
        DiscreteDimension,
        OrdinalDimension,
        CategoricalDimension,
        CompositeDimension,
    }

    public interface IDimension
    {
    }

    public class EmptyDimension : IDimension
    {
        public enum ContainedType
        {
            ContinuousDimension,
            DiscreteDimension,
            OrdinalDimension,
            CategoricalDimension,
        }

        public DimensionTypeName ObjectType { get; set; }
        public string Name { get; set; }
        public ContainedType Type { get; set; }
        public EmptyDimension(string name, ContainedType containedType)
        {
            ObjectType = DimensionTypeName.EmptyDimension;
            Name = name;
            Type = containedType;
        }
    }

    public sealed class ContinuousDimension : IDimension
    {
        public DimensionTypeName ObjectType { get; set; }
        public string Name { get; set; }
        public double Min { get; set; }
        public double Max { get; set; }
        public bool IncludeMin { get; set; }
        public bool IncludeMax { get; set; }

        public ContinuousDimension(string name, double min, double max, bool includeMin = true, bool includeMax = true)
        {
            ObjectType = DimensionTypeName.ContinuousDimension;
            Name = name;
            Min = min;
            Max = max;
            IncludeMin = includeMin;
            IncludeMax = includeMax;
        }
    }

    public class DiscreteDimension : IDimension
    {
        public DimensionTypeName ObjectType { get; set; } // TODO: private setter, read only, make sure works with serializer, move to base class
        public string Name { get; set; }
        public long Min { get; set; }
        public long Max { get; set; }

        public DiscreteDimension(string name, long min, long max)
        {
            ObjectType = DimensionTypeName.DiscreteDimension;
            Name = name;
            Min = min;
            Max = max;
        }
    }

    public class OrdinalDimension : IDimension
    {
        public DimensionTypeName ObjectType { get; set; }
        public string Name { get; set; }
        public List<object> OrderedValues { get; }
        public bool Ascending { get; set; }

        public OrdinalDimension(string name, List<object> orderedValues, bool ascending)
        {
            ObjectType = DimensionTypeName.OrdinalDimension;

            Name = name;

            OrderedValues = orderedValues;

            Ascending = ascending;
        }
    }

    public class CategoricalDimension : IDimension
    {
        public DimensionTypeName ObjectType { get; set; }
        public string Name { get; set; }
        public List<object> Values { get; }

        public CategoricalDimension(string name, List<object> values)
        {
            ObjectType = DimensionTypeName.CategoricalDimension;
            Name = name;
            Values = values;
        }
    }
}
