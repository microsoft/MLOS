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
using System.Text.Json;
using System.Text.Json.Serialization;

using Mlos.Model.Services.Spaces;
using Mlos.Model.Services.Spaces.JsonConverters;

using Python.Runtime;
using Xunit;

namespace Mlos.Model.Services.UnitTests
{
    internal class PythonScriptsAndJsons
    {
        private const string RelativePathToCreateDimensionScript = @"PythonScripts\create_dimensions_and_spaces.py";
        private const string RelativePathToDeserializeDimensionsScript = @"PythonScripts\deserialize_dimensions.py";
        private const string RelativePathToDeserializeSimpleHypergridScript = @"PythonScripts\deserialize_simple_hypergrid.py";
        private const string RelativePathToValidateReserializedHypergridScript = @"PythonScripts\validate_reserialized_hypergrid.py";

        // FIXME: These json files are currently missing in the repo:
        private const string RelativePathToSpinlockSearchSpaceJson = @"JSONs\SpinlockSearchSpace.json";

        private static string createDimensionsScript = null;
        private static string deserializeDimensionsScript = null;
        private static string deserializeSimpleHypergridScript = null;
        private static string validateReserializedHypergridScript = null;
        private static string spinlockSearchSpaceJson = null;

        public static string CreateDimensionsAndSpacesScript
        {
            get
            {
                if (createDimensionsScript is null)
                {
                    createDimensionsScript = File.ReadAllText(Path.Combine(Directory.GetCurrentDirectory(), RelativePathToCreateDimensionScript));
                }

                return createDimensionsScript;
            }
        }

        public static string DeserializeDimensionsScript
        {
            get
            {
                if (deserializeDimensionsScript is null)
                {
                    deserializeDimensionsScript = File.ReadAllText(Path.Combine(Directory.GetCurrentDirectory(), RelativePathToDeserializeDimensionsScript));
                }

                return deserializeDimensionsScript;
            }
        }

        public static string DeserializeSimpleHypergridScript
        {
            get
            {
                if (deserializeSimpleHypergridScript is null)
                {
                    deserializeSimpleHypergridScript = File.ReadAllText(Path.Combine(Directory.GetCurrentDirectory(), RelativePathToDeserializeSimpleHypergridScript));
                }

                return deserializeSimpleHypergridScript;
            }
        }

        public static string ValidateReserializedHypergridScript
        {
            get
            {
                if (validateReserializedHypergridScript is null)
                {
                    validateReserializedHypergridScript = File.ReadAllText(Path.Combine(Directory.GetCurrentDirectory(), RelativePathToValidateReserializedHypergridScript));
                }

                return validateReserializedHypergridScript;
            }
        }

        public static string SpinlockSearchSpaceJson
        {
            get
            {
                if (spinlockSearchSpaceJson is null)
                {
                    spinlockSearchSpaceJson = File.ReadAllText(Path.Combine(Directory.GetCurrentDirectory(), RelativePathToSpinlockSearchSpaceJson));
                }

                return spinlockSearchSpaceJson;
            }
        }
    }

    public class TestOptimizerServiceEncoderDecoder
    {
        private Client.OptimizerServiceEncoder encoder = new Client.OptimizerServiceEncoder();
        private Client.OptimizerServiceDecoder decoder = new Client.OptimizerServiceDecoder();

        // This function is required because Assert.Contains uses the == equivalence relation rather than .Equals()
        private void AssertCollectionSubset(ReadOnlyCollection<object> list1, ReadOnlyCollection<object> list2)
        {
            foreach (var item1 in list1)
            {
                bool sucessfulSearch = false;
                string exceptionMsg = "Unable to find " + item1 + " (" + item1.GetType() + ") in list: ";
                foreach (var item2 in list2)
                {
                    sucessfulSearch = item2.Equals(item1) ? true : sucessfulSearch;
                    exceptionMsg += item2 + " (" + item2.GetType() + "),";
                }

                Assert.True(sucessfulSearch, exceptionMsg);
            }
        }

        // This function is required because Assert.Contains uses the == equivalence relation rather than .Equals()
        // Note: A == B iff A \subset B and B \subset A
        private void AssertCollectionEquality(ReadOnlyCollection<object> list1, ReadOnlyCollection<object> list2)
        {
            AssertCollectionSubset(list1, list2);
            AssertCollectionSubset(list2, list1);
        }

        [Fact]
        [Trait("Category", "SkipForCI")]
        public void TestEmptyDimension()
        {
            var emptyDimension = new EmptyDimension("Empty", DimensionTypeName.OrdinalDimension);
            var serialized0 = encoder.EncodeEmptyDimension(emptyDimension);
            var deserialized0 = decoder.DecodeEmptyDimension(serialized0);

            Assert.Equal(deserialized0.Name, emptyDimension.Name);
            Assert.True(deserialized0.ObjectType.Equals(emptyDimension.ObjectType));

            var serialized = encoder.EncodeDimension(emptyDimension);
            var deserialized = decoder.DecodeDimension(serialized);

            Assert.True(deserialized is EmptyDimension);
            if (deserialized is EmptyDimension deserializedEmpty)
            {
                Assert.Equal(deserializedEmpty.Name, emptyDimension.Name);
                Assert.True(deserializedEmpty.ObjectType.Equals(emptyDimension.ObjectType));
            }
        }

        [Fact]
        [Trait("Category", "SkipForCI")]
        public void TestCategoricalDimension()
        {
            object[] data = { "str", string.Empty, "cat", false, 9.12 };
            var dimension = new CategoricalDimension("Dimension test", "str", string.Empty, "cat", false, 9.12);
            var serialized = encoder.EncodeCategoricalDimension(dimension);
            var deserialized = decoder.DecodeCategoricalDimension(serialized);

            Assert.Equal(deserialized.Name, dimension.Name);
            AssertCollectionEquality(new ReadOnlyCollection<object>(data), deserialized.Values);
        }

        [Fact]
        [Trait("Category", "SkipForCI")]
        public void TestContinuousDimension()
        {
            var dimension = new ContinuousDimension("Test_Continuous \0", -150, 12.24, false, true);
            var serialized = encoder.EncodeContinuousDimension(dimension);
            var deserialized = decoder.DecodeContinuousDimension(serialized);
            Assert.Equal(deserialized.Name, dimension.Name);
            Assert.Equal(deserialized.IncludeMax, dimension.IncludeMax);
            Assert.Equal(deserialized.IncludeMin, dimension.IncludeMin);
            Assert.Equal(deserialized.Max, dimension.Max);
            Assert.Equal(deserialized.Min, dimension.Min);
            Assert.True(deserialized.ObjectType == dimension.ObjectType);
        }

        [Fact]
        [Trait("Category", "SkipForCI")]
        public void TestDiscreteDimension()
        {
            var dimension = new DiscreteDimension("_%% \n \t \\//", long.MinValue, long.MaxValue);
            var serialized = encoder.EncodeDiscreteDimension(dimension);
            var deserialized = decoder.DecodeDiscreteDimension(serialized);

            Assert.Equal(deserialized.Name, dimension.Name);
            Assert.Equal(deserialized.Min, dimension.Min);
            Assert.Equal(deserialized.Max, dimension.Max);
        }

        [Fact]
        [Trait("Category", "SkipForCI")]
        public void TestOrdinalDimension()
        {
            var data = new object[] { "the", false, "brown", "fox", 8, "the", "lazy", "dog" };
            var dimension = new OrdinalDimension("ordinal test", false, data);
            var serialized = encoder.EncodeOrdinalDimension(dimension);
            var deserialized = decoder.DecodeOrdinalDimension(serialized);

            Assert.Equal(dimension.Name, deserialized.Name);
            AssertCollectionEquality(deserialized.OrderedValues, new ReadOnlyCollection<object>(data));
        }

        [Fact]
        [Trait("Category", "SkipForCI")]
        public void TestHypergrid()
        {
            var dataDim1 = new object[] { "a", "b", false, 2, 5.8, "c " };
            var dim0 = new CategoricalDimension("dim0", false, "a", "b", false, 2, 5.8, "c ");
            var dim1 = new ContinuousDimension("dim1", 0, 10.2, false, true);
            var hypergrid = new Hypergrid("hypergrid", dim0, dim1);
            var serialized = encoder.EncodeHypergrid(hypergrid);
            var deserialized = decoder.DecodeHypergrid(serialized);
            Assert.Equal(deserialized.Name, hypergrid.Name);
            Assert.True(deserialized.Dimensions[0] is CategoricalDimension);
            Assert.True(deserialized.Dimensions[1] is ContinuousDimension);

            AssertCollectionEquality(
                ((CategoricalDimension)deserialized.Dimensions[0]).Values,
                ((CategoricalDimension)hypergrid.Dimensions[0]).Values);
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
        [Trait("Category", "SkipForCI")]
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
            var serialized = encoder.EncodeOptimizationProblem(optimizationProblem);
            var deserialized = decoder.DecodeOptimizationProblem(serialized);

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
        [Trait("Category", "SkipForCI")]
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
            var optimizationProblem = new OptimizationProblem(inputHypergrid, objectiveHypergrid, objectives); ;
            var serialized = encoder.EncodeOptimizationProblem(optimizationProblem);
            var deserialized = decoder.DecodeOptimizationProblem(serialized);
            Assert.Null(deserialized.ContextSpace);
        }
    }

    /*
    public class TestSerializingAndDeserializing
    {
        private readonly ContinuousDimension continuous;
        private DiscreteDimension discrete;
        private OrdinalDimension ordinal;
        private CategoricalDimension categorical;
        private Hypergrid allKindsOfDimensions;

        public TestSerializingAndDeserializing()
        {
            // FIXME: This needs better cross-plat support and error handling.
            // - We should include C:\Python37 as another PYTHONHOME location to look for by default
            // - Currently this doesn't handle Linux very well
            // - On Ubuntu Python 3.7 needs to be installed from a separate
            //   repo, which installs as libpython3.7m.so which fails tobe
            //   found due to the trailing "m".
            string pathToVirtualEnv = Environment.GetEnvironmentVariable("PYTHONHOME");

            if (string.IsNullOrEmpty(pathToVirtualEnv))
            {
                pathToVirtualEnv = @"c:\ProgramData\Anaconda3";
            }
            else
            {
                Environment.SetEnvironmentVariable("PYTHONHOME", pathToVirtualEnv, EnvironmentVariableTarget.Process);
            }

            string pathToPythonPkg = $"{pathToVirtualEnv}\\pkgs\\python-3.7.4-h5263a28_0";

            Environment.SetEnvironmentVariable("PATH", $"{pathToVirtualEnv};{pathToPythonPkg}", EnvironmentVariableTarget.Process);
            Environment.SetEnvironmentVariable("PYTHONPATH", $"{pathToVirtualEnv}\\Lib\\site-packages;{pathToVirtualEnv}\\Lib", EnvironmentVariableTarget.Process);

            continuous = new ContinuousDimension(name: "continuous", min: 1, max: 10);
            discrete = new DiscreteDimension(name: "discrete", min: 1, max: 10);
            ordinal = new OrdinalDimension(name: "ordinal", orderedValues: new List<object>() { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 }, ascending: true);
            categorical = new CategoricalDimension(name: "categorical", values: new List<object>() { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 });
            allKindsOfDimensions = new Hypergrid(
                name: "all_kinds_of_dimensions",
                dimensions: new IDimension[]
                {
                    continuous,
                    discrete,
                    ordinal,
                    categorical,
                });
        }

        [Fact]
        [Trait("Category", "SkipForCI")]
        public void TestSerializingSimpleHypergrid()
        {
            string originalValidSimpleHypergridJsonString = PythonScriptsAndJsons.SpinlockSearchSpaceJson;

            Hypergrid spinlockSearchSpace = new Hypergrid(
                "SpinlockSearchSpace",
                new DiscreteDimension(name: "shortBackOffMilliSeconds", min: 1, max: 1 << 20),
                new DiscreteDimension(name: "longBackOffMilliSeconds", min: 1, max: 1 << 20),
                new DiscreteDimension(name: "longBackOffWaitMilliSeconds", min: 1, max: 1 << 20),
                new DiscreteDimension(name: "minSpinCount", min: 1, max: 1 << 20),
                new DiscreteDimension(name: "maxSpinCount", min: 1, max: 1 << 20),
                new DiscreteDimension(name: "maxbackOffAttempts", min: 1, max: 1 << 20),
                new DiscreteDimension(name: "acquireSpinCount", min: 1, max: 1 << 20),
                new CategoricalDimension(name: "algorithm", values: new[] { "Optimistic", "ExponentialBackoff" }));
            var jsonSerializerOptions = new JsonSerializerOptions
            {
                WriteIndented = true,
                Converters =
                {
                    new JsonStringEnumConverter(),
                    new HypergridJsonConverter(),
                    new DimensionJsonConverter(),
                },
            };

            string serializedJsonString = JsonSerializer.Serialize(spinlockSearchSpace, jsonSerializerOptions);
            Assert.Equal(originalValidSimpleHypergridJsonString, serializedJsonString);

            string yetAnotherSerializedJsonString = spinlockSearchSpace.ToJson();
            Assert.Equal(originalValidSimpleHypergridJsonString, yetAnotherSerializedJsonString);
        }

        [Fact]
        [Trait("Category", "SkipForCI")]
        public void TestPythonInterop()
        {
            var jsonSerializerOptions = new JsonSerializerOptions
            {
                WriteIndented = true,
                Converters =
                {
                    new JsonStringEnumConverter(),
                    new HypergridJsonConverter(),
                    new DimensionJsonConverter(),
                },
            };

            string csContinuousJsonString = JsonSerializer.Serialize(continuous, jsonSerializerOptions);
            string csDiscreteJsonString = JsonSerializer.Serialize(discrete, jsonSerializerOptions);
            string csOrdinalJsonString = JsonSerializer.Serialize(ordinal, jsonSerializerOptions);
            string csCategoricalJsonString = JsonSerializer.Serialize(categorical, jsonSerializerOptions);
            string csSimpleHypergridJsonString = JsonSerializer.Serialize(allKindsOfDimensions, jsonSerializerOptions);

            using (Py.GIL())
            {
                using PyScope pythonScope = Py.CreateScope();

                pythonScope.Set("cs_continuous_dimension_json_string", csContinuousJsonString);
                pythonScope.Set("cs_discrete_dimension_json_string", csDiscreteJsonString);
                pythonScope.Set("cs_ordinal_dimension_json_string", csOrdinalJsonString);
                pythonScope.Set("cs_categorical_dimension_json_string", csCategoricalJsonString);
                pythonScope.Set("cs_simple_hypergrid_json_string", csSimpleHypergridJsonString);

                pythonScope.Exec(PythonScriptsAndJsons.CreateDimensionsAndSpacesScript);
                pythonScope.Exec(PythonScriptsAndJsons.DeserializeDimensionsScript);

                bool successfullyDeserializedDimensions = pythonScope.Get("success").As<bool>();
                string exceptionMessage = string.Empty;
                if (!successfullyDeserializedDimensions)
                {
                    exceptionMessage = pythonScope.Get("exception_message").As<string>();
                }

                Assert.True(successfullyDeserializedDimensions, exceptionMessage);

                pythonScope.Exec(PythonScriptsAndJsons.DeserializeSimpleHypergridScript);

                bool successfullyDeserializedSimpleHypergrid = pythonScope.Get("success").As<bool>();
                if (!successfullyDeserializedSimpleHypergrid)
                {
                    exceptionMessage = pythonScope.Get("exception_message").As<string>();
                }

                Assert.True(successfullyDeserializedSimpleHypergrid, exceptionMessage);

                string pySimpleHypergridJsonString = pythonScope.Get("py_simple_hypergrid_json_string").As<string>();
                Hypergrid simpleHypergridDeserializedFromPython = JsonSerializer.Deserialize<Hypergrid>(pySimpleHypergridJsonString, jsonSerializerOptions);

                Assert.True(simpleHypergridDeserializedFromPython.Name == "all_kinds_of_dimensions");
                Assert.True(simpleHypergridDeserializedFromPython.Dimensions.Count == 4);

                string reserializedHypergrid = JsonSerializer.Serialize(simpleHypergridDeserializedFromPython, jsonSerializerOptions);

                pythonScope.Set("cs_reserialized_hypergrid_json_string", reserializedHypergrid);
                pythonScope.Exec(PythonScriptsAndJsons.ValidateReserializedHypergridScript);

                bool successfullyValidatedReserializedHypergrid = pythonScope.Get("success").As<bool>();
                if (!successfullyValidatedReserializedHypergrid)
                {
                    exceptionMessage = pythonScope.Get("exception_message").As<string>();
                }

                Assert.True(successfullyValidatedReserializedHypergrid, exceptionMessage);
            }

            string currentDirectory = Directory.GetCurrentDirectory();
            Console.WriteLine($"Current directory {currentDirectory}");
        }

        [Fact]
        [Trait("Category", "SkipForCI")]
        public void TestNewConverter()
        {
            JsonSerializerOptions options = new JsonSerializerOptions
            {
                WriteIndented = true,
                Converters =
                {
                    new HypergridJsonConverter(),
                    new DimensionJsonConverter(),
                },
            };

            var json = JsonSerializer.Serialize<Hypergrid>(allKindsOfDimensions, options);
            string serializedHypergrid = allKindsOfDimensions.ToJson();

            var deserializedSimpleHypergrid = JsonSerializer.Deserialize<Hypergrid>(serializedHypergrid, options);
        }
    }
    */
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
