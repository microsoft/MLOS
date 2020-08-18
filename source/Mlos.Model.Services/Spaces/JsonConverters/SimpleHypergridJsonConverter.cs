// -----------------------------------------------------------------------
// <copyright file="SimpleHypergridJsonConverter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Mlos.Model.Services.Spaces.JsonConverters
{
    public class SimpleHypergridJsonConverter : JsonConverterWithExpectations<SimpleHypergrid>
    {
        public override SimpleHypergrid Read(
            ref Utf8JsonReader reader,
            Type typeToConvert,
            JsonSerializerOptions options)
        {
            string hypergridName;
            List<IDimension> dimensions = new List<IDimension>();
            Expect(ref reader, expectedTokenType: JsonTokenType.PropertyName, expectedTokenValue: "ObjectType");
            Expect(ref reader, expectedTokenType: JsonTokenType.String, expectedTokenValue: "SimpleHypergrid");
            Expect(ref reader, expectedTokenType: JsonTokenType.PropertyName, expectedTokenValue: "Name");
            Expect(ref reader, expectedTokenType: JsonTokenType.String);
            hypergridName = reader.GetString();
            Expect(ref reader, expectedTokenType: JsonTokenType.PropertyName, expectedTokenValue: "Dimensions");
            Expect(ref reader, expectedTokenType: JsonTokenType.StartArray);

            // Let's get the right converter
            //
            DimensionJsonConverter dimensionJsonConverter = null;
            for (int i = 0; i < options.Converters.Count; i++)
            {
                if (options.Converters[i].GetType() == typeof(DimensionJsonConverter))
                {
                    dimensionJsonConverter = (DimensionJsonConverter)options.Converters[i];
                    break;
                }
            }

            if (dimensionJsonConverter is null)
            {
                dimensionJsonConverter = new DimensionJsonConverter();
            }

            while (PeakNextTokenType(reader) == JsonTokenType.StartObject)
            {
                IDimension dimension = dimensionJsonConverter.Read(ref reader, typeof(IDimension), options);
                dimensions.Add(dimension);
            }

            Expect(ref reader, expectedTokenType: JsonTokenType.EndArray);
            Expect(ref reader, expectedTokenType: JsonTokenType.EndObject);

            return new SimpleHypergrid(name: hypergridName, dimensions: dimensions);
        }

        public override void Write(
            Utf8JsonWriter writer,
            SimpleHypergrid value,
            JsonSerializerOptions options)
        {
            writer.WriteStartObject();
            writer.WriteString("ObjectType", "SimpleHypergrid");
            writer.WriteString("Name", value.Name);
            writer.WritePropertyName("Dimensions");
            writer.WriteStartArray();

            for (int i = 0; i < value.Dimensions.Count; i++)
            {
                IDimension dimension = value.Dimensions[i];
                JsonSerializer.Serialize(writer, dimension, options);
            }

            writer.WriteEndArray();
            writer.WriteEndObject();
        }
    }
}
