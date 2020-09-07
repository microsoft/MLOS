// -----------------------------------------------------------------------
// <copyright file="HypergridJsonConverter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;

namespace Mlos.Model.Services.Spaces.JsonConverters
{
    public class HypergridJsonConverter : JsonConverterWithExpectations<Hypergrid>
    {
        /// <inheritdoc/>
        public override Hypergrid Read(
            ref Utf8JsonReader reader,
            Type typeToConvert,
            JsonSerializerOptions options)
        {
            var dimensions = new List<IDimension>();

            Expect(ref reader, expectedTokenType: JsonTokenType.PropertyName, expectedTokenValue: "ObjectType");
            Expect(ref reader, expectedTokenType: JsonTokenType.String, expectedTokenValue: "SimpleHypergrid");
            Expect(ref reader, expectedTokenType: JsonTokenType.PropertyName, expectedTokenValue: "Name");
            Expect(ref reader, expectedTokenType: JsonTokenType.String);
            string hypergridName = reader.GetString();
            Expect(ref reader, expectedTokenType: JsonTokenType.PropertyName, expectedTokenValue: "Dimensions");
            Expect(ref reader, expectedTokenType: JsonTokenType.StartArray);

            // Deserialize dimensions.
            //
            JsonConverterWithExpectations<IDimension> dimensionJsonConverter = (JsonConverterWithExpectations<IDimension>)options.GetConverter(typeof(IDimension));

            while (PeekNextTokenType(reader) == JsonTokenType.StartObject)
            {
                IDimension dimension = dimensionJsonConverter.Read(ref reader, typeof(IDimension), options);
                dimensions.Add(dimension);
            }

            Expect(ref reader, expectedTokenType: JsonTokenType.EndArray);

            // Optionally deserialize the subgrids.
            //
            Dictionary<string, HashSet<Hypergrid.SubgridJoin>> subgrids = null;

            if (PeekNextTokenType(reader) == JsonTokenType.PropertyName)
            {
                Expect(ref reader, expectedTokenType: JsonTokenType.PropertyName, expectedTokenValue: "GuestSubgrids");

                var converter = new JsonDictionaryConverter<string, HashSet<Hypergrid.SubgridJoin>>();

                subgrids = converter.Read(ref reader, typeof(Dictionary<string, HashSet<Hypergrid.SubgridJoin>>), options);
            }

            Expect(ref reader, expectedTokenType: JsonTokenType.EndObject);

            return new Hypergrid(name: hypergridName, dimensions: dimensions.ToArray(), subgrids: subgrids);
        }

        /// <inheritdoc/>
        public override void Write(
            Utf8JsonWriter writer,
            Hypergrid value,
            JsonSerializerOptions options)
        {
            writer.WriteStartObject();
            writer.WriteString("ObjectType", "SimpleHypergrid");
            writer.WriteString("Name", value.Name);

            // Write Dimensions.
            //
            writer.WritePropertyName("Dimensions");
            writer.WriteStartArray();

            for (int i = 0; i < value.Dimensions.Count; i++)
            {
                IDimension dimension = value.Dimensions[i];
                JsonSerializer.Serialize(writer, dimension, options);
            }

            writer.WriteEndArray();

            // Write subgrids.
            //
            if (value.Subgrids != null &&
                value.Subgrids.Any())
            {
                writer.WritePropertyName("GuestSubgrids");

                JsonSerializer.Serialize(writer, value.Subgrids, options);
            }

            writer.WriteEndObject();
        }
    }
}
