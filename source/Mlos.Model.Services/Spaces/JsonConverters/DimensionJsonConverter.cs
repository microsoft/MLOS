// -----------------------------------------------------------------------
// <copyright file="DimensionJsonConverter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Text.Json;

namespace Mlos.Model.Services.Spaces.JsonConverters
{
    public class DimensionJsonConverter : JsonConverterWithExpectations<IDimension>
    {
        /// <inheritdoc/>
        public override IDimension Read(
            ref Utf8JsonReader reader,
            Type typeToConvert,
            JsonSerializerOptions options)
        {
            string dimensionName;
            string dimensionType;
            Expect(ref reader, expectedTokenType: JsonTokenType.StartObject);
            Expect(ref reader, expectedTokenType: JsonTokenType.PropertyName, expectedTokenValue: "ObjectType");
            Expect(ref reader, expectedTokenType: JsonTokenType.String);
            dimensionType = reader.GetString();
            Expect(ref reader, expectedTokenType: JsonTokenType.PropertyName, expectedTokenValue: "Name");
            Expect(ref reader, expectedTokenType: JsonTokenType.String);
            dimensionName = reader.GetString();

            IDimension dimension = dimensionType switch
            {
                "ContinuousDimension" => DeserializeContinuousDimension(ref reader, dimensionName),
                "DiscreteDimension" => DeserializeDiscreteDimension(ref reader, dimensionName),
                "OrdinalDimension" => DeserializeOrdinalDimension(ref reader, dimensionName),
                "CategoricalDimension" => DeserializeCategoricalDimension(ref reader, dimensionName),
                _ => throw new JsonException($"Unsupported dimensionType:{dimensionType} name:{dimensionName}"),
            };

            return dimension;
        }

        /// <inheritdoc/>
        public override void Write(
            Utf8JsonWriter writer,
            IDimension value,
            JsonSerializerOptions options)
        {
            // Note that the local dimension variable is created by the case statement.
            // it is equivalent to: ```ContinuousDimension dimension = (ContinuousDimension)value;```
            //
            switch (value)
            {
                case ContinuousDimension dimension:
                    JsonSerializer.Serialize(writer, dimension, options);
                    break;
                case DiscreteDimension dimension:
                    JsonSerializer.Serialize(writer, dimension, options);
                    break;
                case OrdinalDimension dimension:
                    JsonSerializer.Serialize(writer, dimension, options);
                    break;
                case CategoricalDimension dimension:
                    JsonSerializer.Serialize(writer, dimension, options);
                    break;
                default:
                    throw new JsonException();
            }
        }

        /// <summary>
        /// Deserializes a JSON of this form into a ContinuousDimension object:
        /// {
        ///   "ObjectType": "ContinuousDimension",
        ///   "Name": "continuous",
        ///   "Min": 1,
        ///   "Max": 10,
        ///   "IncludeMin": true,
        ///   "IncludeMax": true
        /// }.
        /// </summary>
        /// <param name="reader"></param>
        /// <param name="dimensionName"></param>
        /// <returns></returns>
        private ContinuousDimension DeserializeContinuousDimension(ref Utf8JsonReader reader, string dimensionName)
        {
            double min;
            double max;
            bool includeMin;
            bool includeMax;

            Expect(ref reader, JsonTokenType.PropertyName, "Min");
            Expect(ref reader, JsonTokenType.Number);
            min = reader.GetDouble();

            Expect(ref reader, JsonTokenType.PropertyName, "Max");
            Expect(ref reader, JsonTokenType.Number);
            max = reader.GetDouble();

            Expect(ref reader, JsonTokenType.PropertyName, "IncludeMin");
            ExpectBoolean(ref reader);
            includeMin = reader.GetBoolean();

            Expect(ref reader, JsonTokenType.PropertyName, "IncludeMax");
            ExpectBoolean(ref reader);
            includeMax = reader.GetBoolean();

            Expect(ref reader, JsonTokenType.EndObject);

            return new ContinuousDimension(
                name: dimensionName,
                min: min,
                max: max,
                includeMin: includeMin,
                includeMax: includeMax);
        }

        /// <summary>
        /// Deserializes a JSON of the following form into a DiscreteDimension object:
        /// {
        ///   "ObjectType": "DiscreteDimension",
        ///   "Name": "discrete",
        ///   "Min": 1,
        ///   "Max": 10
        /// }.
        /// </summary>
        /// <param name="reader"></param>
        /// <param name="dimensionName"></param>
        /// <returns></returns>
        private DiscreteDimension DeserializeDiscreteDimension(ref Utf8JsonReader reader, string dimensionName)
        {
            long min;
            long max;

            Expect(ref reader, JsonTokenType.PropertyName, "Min");
            Expect(ref reader, JsonTokenType.Number);
            min = reader.GetInt64();

            Expect(ref reader, JsonTokenType.PropertyName, "Max");
            Expect(ref reader, JsonTokenType.Number);
            max = reader.GetInt64();

            Expect(ref reader, JsonTokenType.EndObject);

            return new DiscreteDimension(
                name: dimensionName,
                min: min,
                max: max);
        }

        /// <summary>
        /// Deserializes the following JSON into an OrdinalDimension object.
        /// {
        ///  "ObjectType": "OrdinalDimension",
        ///  "Name": "ordinal",
        ///  "OrderedValues": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        ///  "Ascending": true
        /// }.
        /// </summary>
        /// <param name="reader"></param>
        /// <param name="dimensionName"></param>
        /// <returns></returns>
        private OrdinalDimension DeserializeOrdinalDimension(ref Utf8JsonReader reader, string dimensionName)
        {
            List<object> orderedValues = new List<object>();
            bool ascending;

            Expect(ref reader, JsonTokenType.PropertyName, "OrderedValues");
            Expect(ref reader, JsonTokenType.StartArray);

            JsonTokenType nextTokenType = PeekNextTokenType(reader);
            while ((nextTokenType == JsonTokenType.Number) || (nextTokenType == JsonTokenType.String))
            {
                if (nextTokenType == JsonTokenType.Number)
                {
                    Expect(ref reader, JsonTokenType.Number);
                    orderedValues.Add(reader.GetInt64());
                }
                else
                {
                    Expect(ref reader, JsonTokenType.String);
                    orderedValues.Add(reader.GetString());
                }

                nextTokenType = PeekNextTokenType(reader);
            }

            Expect(ref reader, JsonTokenType.EndArray);
            Expect(ref reader, JsonTokenType.PropertyName, "Ascending");
            ExpectBoolean(ref reader);
            ascending = reader.GetBoolean();

            Expect(ref reader, JsonTokenType.EndObject);
            return new OrdinalDimension(
                name: dimensionName,
                orderedValues: orderedValues,
                ascending: ascending);
        }

        /// <summary>
        /// Deserializes the following JSON into a CategoricalDimensionObject.
        /// {
        ///  "ObjectType": "CategoricalDimension",
        ///  "Name": "categorical",
        ///  "Values": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        /// }.
        /// </summary>
        /// <param name="reader"></param>
        /// <param name="dimensionName"></param>
        /// <returns></returns>
        private CategoricalDimension DeserializeCategoricalDimension(ref Utf8JsonReader reader, string dimensionName)
        {
            var values = new List<object>();
            Expect(ref reader, JsonTokenType.PropertyName, "Values");
            Expect(ref reader, JsonTokenType.StartArray);

            JsonTokenType nextTokenType = PeekNextTokenType(reader);
            while ((nextTokenType == JsonTokenType.Number) || (nextTokenType == JsonTokenType.String))
            {
                if (nextTokenType == JsonTokenType.Number)
                {
                    Expect(ref reader, JsonTokenType.Number);
                    values.Add(reader.GetInt64());
                }
                else
                {
                    Expect(ref reader, JsonTokenType.String);
                    values.Add(reader.GetString());
                }

                nextTokenType = PeekNextTokenType(reader);
            }

            Expect(ref reader, JsonTokenType.EndArray);
            Expect(ref reader, JsonTokenType.EndObject);

            return new CategoricalDimension(
                name: dimensionName,
                values: values);
        }
    }
}
