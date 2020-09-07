// -----------------------------------------------------------------------
// <copyright file="Dimensions.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System.Collections.ObjectModel;

namespace Mlos.Model.Services.Spaces
{
    public enum DimensionTypeName
    {
        ContinuousDimension,
        DiscreteDimension,
        OrdinalDimension,
        CategoricalDimension,
    }

    public interface IDimension
    {
        public string Name { get; set; }
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

        public ReadOnlyCollection<object> OrderedValues { get; }

        public bool Ascending { get; set; }

        public OrdinalDimension(string name, bool ascending, params object[] orderedValues)
        {
            ObjectType = DimensionTypeName.OrdinalDimension;
            Name = name;
            OrderedValues = new ReadOnlyCollection<object>(orderedValues);
            Ascending = ascending;
        }
    }

    public class CategoricalDimension : IDimension
    {
        public DimensionTypeName ObjectType { get; set; }

        public string Name { get; set; }

        public ReadOnlyCollection<object> Values { get; }

        public CategoricalDimension(string name, params object[] values)
        {
            ObjectType = DimensionTypeName.CategoricalDimension;
            Name = name;
            Values = new ReadOnlyCollection<object>(values);
        }
    }
}
