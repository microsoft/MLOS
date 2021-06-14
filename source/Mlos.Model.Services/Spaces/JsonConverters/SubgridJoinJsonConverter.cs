// -----------------------------------------------------------------------
// <copyright file="SubgridJoinJsonConverter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Mlos.Model.Services.Spaces.JsonConverters
{
    internal class SubgridJoinJsonConverter : JsonConverterWithExpectations<SubgridJoin>
    {
        /// <inheritdoc/>
        public override SubgridJoin Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        {
            Expect(ref reader, JsonTokenType.StartObject);

            Expect(ref reader, JsonTokenType.PropertyName, "ObjectType");
            Expect(ref reader, JsonTokenType.String, "GuestSubgrid");

            Expect(ref reader, JsonTokenType.PropertyName, "Subgrid");

            Expect(ref reader, JsonTokenType.StartObject);

            // Subgrid.
            //
            var hypergridConverter = (JsonConverter<Hypergrid>)options.GetConverter(typeof(Hypergrid));
            Hypergrid hypergrid = hypergridConverter.Read(ref reader, typeof(Hypergrid), options);

            // Dimension.
            //
            Expect(ref reader, JsonTokenType.PropertyName, "ExternalPivotDimension");
            var dimensionConverter = (JsonConverter<IDimension>)options.GetConverter(typeof(IDimension));
            IDimension dimension = dimensionConverter.Read(ref reader, typeof(IDimension), options);

            Expect(ref reader, JsonTokenType.EndObject);

            return new SubgridJoin
            {
                OnExternalJoin = dimension,
                Subgrid = hypergrid,
            };
        }

        /// <inheritdoc/>
        public override void Write(Utf8JsonWriter writer, SubgridJoin value, JsonSerializerOptions options)
        {
            writer.WriteStartObject();

            // Subgrid.
            //
            writer.WriteString("ObjectType", "GuestSubgrid");
            writer.WritePropertyName("Subgrid");
            Hypergrid subgrid = (Hypergrid)value.Subgrid;
            JsonSerializer.Serialize(writer, subgrid, options);

            // Dimensions.
            //
            writer.WritePropertyName("ExternalPivotDimension");
            IDimension dimension = value.OnExternalJoin;
            JsonSerializer.Serialize(writer, dimension, options);

            writer.WriteEndObject();
        }
    }
}
