// -----------------------------------------------------------------------
// <copyright file="UnitTests.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;

using Mlos.Model.Services.Client;
using Mlos.Model.Services.Spaces;
using Mlos.Model.Services.Spaces.JsonConverters;
using Python.Runtime;
using Xunit;

namespace Mlos.Model.Services.UnitTests
{
    public class TestOptimizerServiceEncoderDecoder
    {
        [Fact]
        public void TestEmptyDimension()
        {
            var emptyDimension = new EmptyDimension("Empty", DimensionTypeName.OrdinalDimension);
            var serialized0 = OptimizerServiceEncoder.EncodeEmptyDimension(emptyDimension);
            var deserialized0 = OptimizerServiceDecoder.DecodeEmptyDimension(serialized0);

            Assert.Equal(deserialized0.Name, emptyDimension.Name);
            Assert.True(deserialized0.ObjectType.Equals(emptyDimension.ObjectType));

            var serialized = OptimizerServiceEncoder.EncodeDimension(emptyDimension);
            var deserialized = OptimizerServiceDecoder.DecodeDimension(serialized);

            Assert.True(deserialized is EmptyDimension);
            if (deserialized is EmptyDimension deserializedEmpty)
            {
                Assert.Equal(deserializedEmpty.Name, emptyDimension.Name);
                Assert.True(deserializedEmpty.ObjectType.Equals(emptyDimension.ObjectType));
            }
        }

        [Fact]
        public void TestCategoricalDimension()
        {
            object[] data = { "str", string.Empty, "cat", false, 9.12 };
            var dimension = new CategoricalDimension("Dimension test", data);
            var serialized = OptimizerServiceEncoder.EncodeCategoricalDimension(dimension);
            var deserialized = OptimizerServiceDecoder.DecodeCategoricalDimension(serialized);

            Assert.Equal(deserialized.Name, dimension.Name);
            Assert.True(deserialized.Values.SequenceEqual(data));
        }

        [Fact]
        public void TestContinuousDimension()
        {
            var dimension = new ContinuousDimension("Test_Continuous \0", -150, 12.24, false, true);
            var serialized = OptimizerServiceEncoder.EncodeContinuousDimension(dimension);
            var deserialized = OptimizerServiceDecoder.DecodeContinuousDimension(serialized);
            Assert.Equal(deserialized.Name, dimension.Name);
            Assert.Equal(deserialized.IncludeMax, dimension.IncludeMax);
            Assert.Equal(deserialized.IncludeMin, dimension.IncludeMin);
            Assert.Equal(deserialized.Max, dimension.Max);
            Assert.Equal(deserialized.Min, dimension.Min);
            Assert.True(deserialized.ObjectType == dimension.ObjectType);
        }

        [Fact]
        public void TestDiscreteDimension()
        {
            var dimension = new DiscreteDimension("_%% \n \t \\//", long.MinValue, long.MaxValue);
            var serialized = OptimizerServiceEncoder.EncodeDiscreteDimension(dimension);
            var deserialized = OptimizerServiceDecoder.DecodeDiscreteDimension(serialized);

            Assert.Equal(deserialized.Name, dimension.Name);
            Assert.Equal(deserialized.Min, dimension.Min);
            Assert.Equal(deserialized.Max, dimension.Max);
        }

        [Fact]
        public void TestOrdinalDimension()
        {
            object[] data = new object[] { "the", false, "brown", "fox", 8, "the", "lazy", "dog" };
            var dimension = new OrdinalDimension("ordinal test", false, data);
            var serialized = OptimizerServiceEncoder.EncodeOrdinalDimension(dimension);
            var deserialized = OptimizerServiceDecoder.DecodeOrdinalDimension(serialized);

            Assert.Equal(dimension.Name, deserialized.Name);
            Assert.True(deserialized.OrderedValues.SequenceEqual(data));
            Assert.False(deserialized.OrderedValues.SequenceEqual(new object[] { "ensure failure" }));
        }

        [Fact]
        public void TestHypergrid()
        {
            var dataDim1 = new object[] { "a", "b", false, 2, 5.8, "c " };
            var dim0 = new CategoricalDimension("dim0", false, "a", "b", false, 2, 5.8, "c ");
            var dim1 = new ContinuousDimension("dim1", 0, 10.2, false, true);
            var hypergrid = new Hypergrid("hypergrid", dim0, dim1);
            var serialized = OptimizerServiceEncoder.EncodeHypergrid(hypergrid);
            var deserialized = OptimizerServiceDecoder.DecodeHypergrid(serialized);
            Assert.Equal(deserialized.Name, hypergrid.Name);
            Assert.True(deserialized.Dimensions[0] is CategoricalDimension);
            Assert.True(deserialized.Dimensions[1] is ContinuousDimension);

            Assert.True(
                ((CategoricalDimension)deserialized.Dimensions[0]).Values.SequenceEqual(
                ((CategoricalDimension)hypergrid.Dimensions[0]).Values));
            Assert.Equal(
                ((ContinuousDimension)deserialized.Dimensions[1]).Name,
                dim1.Name);
            Assert.Equal(
                ((ContinuousDimension)deserialized.Dimensions[1]).Min,
                dim1.Min);
            Assert.Equal(
               ((ContinuousDimension)deserialized.Dimensions[1]).Max,
               dim1.Max);
            Assert.Equal(
               ((ContinuousDimension)deserialized.Dimensions[1]).IncludeMin,
               dim1.IncludeMin);
            Assert.Equal(
               ((ContinuousDimension)deserialized.Dimensions[1]).IncludeMax,
               dim1.IncludeMax);
        }

        [Fact]
        public void TestOptimizationProblemContext()
        {
            var in1 = new ContinuousDimension("in_1", 0, 10);
            var in2 = new DiscreteDimension("in_2", 1, 20);
            var inputHypergrid = new Hypergrid("input", in1, in2);
            var out1 = new ContinuousDimension("out_1", -5, 7);
            var objectiveHypergrid = new Hypergrid("output", out1);
            var context1 = new DiscreteDimension("ctx_1", -100, -0);
            var contextHypergrid = new Hypergrid("context", context1);
            var objectives = new OptimizationObjective[]
            {
                new OptimizationObjective("out_1", true),
                new OptimizationObjective("nonExistent", false),
            };
            var optimizationProblem = new OptimizationProblem(inputHypergrid, contextHypergrid, objectiveHypergrid, objectives);
            var serialized = OptimizerServiceEncoder.EncodeOptimizationProblem(optimizationProblem);
            var deserialized = OptimizerServiceDecoder.DecodeOptimizationProblem(serialized);

            Assert.Equal(optimizationProblem.ParameterSpace.Name, deserialized.ParameterSpace.Name);
            Assert.Equal(optimizationProblem.ObjectiveSpace.Name, deserialized.ObjectiveSpace.Name);
            Assert.Equal(optimizationProblem.ContextSpace.Name, deserialized.ContextSpace.Name);

            Assert.Equal(optimizationProblem.Objectives[0].Name, objectives[0].Name);
            Assert.Equal(optimizationProblem.Objectives[0].Minimize, objectives[0].Minimize);
            Assert.Equal(optimizationProblem.Objectives[1].Name, objectives[1].Name);
            Assert.Equal(optimizationProblem.Objectives[1].Minimize, objectives[1].Minimize);

            // This is not a rigorous test but it should be sufficient given the other tests in this set.
            Assert.Equal(optimizationProblem.ParameterSpace.Dimensions[0].Name, deserialized.ParameterSpace.Dimensions[0].Name);
            Assert.Equal(optimizationProblem.ParameterSpace.Dimensions[1].Name, deserialized.ParameterSpace.Dimensions[1].Name);
            Assert.Equal(optimizationProblem.ObjectiveSpace.Dimensions[0].Name, deserialized.ObjectiveSpace.Dimensions[0].Name);
            Assert.Equal(optimizationProblem.ContextSpace.Dimensions[0].Name, deserialized.ContextSpace.Dimensions[0].Name);
        }

        [Fact]
        public void TestOptimizationProblemNoContext()
        {
            var in1 = new ContinuousDimension("in_1", 0, 10);
            var in2 = new DiscreteDimension("in_2", 1, 20);
            var inputHypergrid = new Hypergrid("input", in1, in2);
            var out1 = new ContinuousDimension("out_1", -5, 7);
            var objectiveHypergrid = new Hypergrid("output", out1);
            var objectives = new OptimizationObjective[]
            {
                new OptimizationObjective("out_1", true),
                new OptimizationObjective("nonExistent", false),
            };
            var optimizationProblem = new OptimizationProblem(inputHypergrid, objectiveHypergrid, objectives);
            var serialized = OptimizerServiceEncoder.EncodeOptimizationProblem(optimizationProblem);
            var deserialized = OptimizerServiceDecoder.DecodeOptimizationProblem(serialized);
            Assert.Null(deserialized.ContextSpace);
        }

        [Fact]
        public void TestOptimizationProblemSubgridObjectives()
        {
            Hypergrid cacheSearchSpace = new Hypergrid(
                name: "smart_cache_config",
                dimension: new CategoricalDimension("cache_implementation", 0, 1))
            .Join(
                subgrid: new Hypergrid(
                    name: "lru_cache_config",
                    dimension: new DiscreteDimension("cache_size", min: 1, max: 1 << 12)),
                onExternalDimension: new CategoricalDimension("cache_implementation", 0))
            .Join(
                subgrid: new Hypergrid(
                    name: "mru_cache_config",
                    dimension: new DiscreteDimension("cache_size", min: 1, max: 1 << 12)),
                onExternalDimension: new CategoricalDimension("cache_implementation", 1));

            var optimizationProblem = new OptimizationProblem
            {
                ParameterSpace = cacheSearchSpace,
                ContextSpace = null,
                ObjectiveSpace = new Hypergrid(
                    name: "objectives",
                    dimensions: new ContinuousDimension(name: "HitRate", min: 0.0, max: 1.0)),
            };

            optimizationProblem.Objectives.Add(
                new OptimizationObjective(name: "HitRate", minimize: false));

            var serialized = OptimizerServiceEncoder.EncodeOptimizationProblem(optimizationProblem);
            var deserialized = OptimizerServiceDecoder.DecodeOptimizationProblem(serialized);

            Assert.True(deserialized.Objectives.Count == 1);
            Assert.Equal(deserialized.Objectives[0].Name, optimizationProblem.Objectives[0].Name);
            Assert.True(deserialized.ObjectiveSpace.Dimensions.Count == 1);
        }
    }

    public class DummyTest
    {
        [Fact]
        public void TestDummy()
        {
            // This test is only here to let the xunit adapter find some test
            // to run so that "dotnet test" passes even though we by default
            // exclude the "SkipForCI" category tests above (which is all of them)
            // for the moment
        }
    }
}
