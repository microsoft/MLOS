// -----------------------------------------------------------------------
// <copyright file="HashSetJsonConverter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Mlos.Model.Services.Spaces.JsonConverters
{
    internal class HashSetJsonConverter<T> : JsonConverterWithExpectations<HashSet<T>>
    {
        /// <inheritdoc/>
        public override HashSet<T> Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        {
            Expect(ref reader, JsonTokenType.StartArray);

            var converter = (JsonConverter<T>)options.GetConverter(typeof(T));

            var value = new HashSet<T>();

            // If available, deseralize object from the string and add to the collection.
            //
            while (PeekNextTokenType(reader) == JsonTokenType.StartObject)
            {
                T element = converter.Read(ref reader, typeof(T), options);
                value.Add(element);
            }

            Expect(ref reader, JsonTokenType.EndArray);

            return value;
        }

        /// <inheritdoc/>
        public override void Write(Utf8JsonWriter writer, HashSet<T> value, JsonSerializerOptions options)
        {
            writer.WriteString("ObjectType", "set");

            writer.WritePropertyName("Values");

            writer.WriteStartArray();

            foreach (var element in value)
            {
                JsonSerializer.Serialize(writer, element, options);
            }

            writer.WriteEndArray();
        }
    }
}
