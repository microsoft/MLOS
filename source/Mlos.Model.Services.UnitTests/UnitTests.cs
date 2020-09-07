// -----------------------------------------------------------------------
// <copyright file="UnitTests.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
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

    public class TestSerializingAndDeserializing
    {
        private readonly ContinuousDimension continuous;
        private DiscreteDimension discrete;
        private OrdinalDimension ordinal;
        private CategoricalDimension categorical;
        private Hypergrid allKindsOfDimensions;

        public TestSerializingAndDeserializing()
        {
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
}
