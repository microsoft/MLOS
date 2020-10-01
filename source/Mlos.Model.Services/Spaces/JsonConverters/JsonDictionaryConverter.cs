// -----------------------------------------------------------------------
// <copyright file="JsonDictionaryConverter.cs" company="Microsoft Corporation">
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
    public class JsonDictionaryConverter<TKey, TValue> : JsonConverterWithExpectations<Dictionary<TKey, TValue>>
    {
        /// <inheritdoc/>
        public override Dictionary<TKey, TValue> Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        {
            Expect(ref reader, expectedTokenType: JsonTokenType.StartObject);

            var value = new Dictionary<TKey, TValue>();

            while (PeekNextTokenType(reader) == JsonTokenType.PropertyName)
            {
                Expect(ref reader, JsonTokenType.PropertyName);

                JsonConverter<TKey> keyConverter = (JsonConverter<TKey>)options.GetConverter(typeof(TKey));
                TKey key = keyConverter.Read(ref reader, typeof(TKey), options);

                Expect(ref reader, JsonTokenType.StartObject);

                Expect(ref reader, JsonTokenType.PropertyName, "ObjectType");
                Expect(ref reader, JsonTokenType.String, "set");

                Expect(ref reader, JsonTokenType.PropertyName, "Values");

                JsonConverter<TValue> valueConverter = (JsonConverter<TValue>)options.GetConverter(typeof(TValue));
                TValue element = valueConverter.Read(ref reader, typeof(TValue), options);

                value.Add(key, element);

                Expect(ref reader, JsonTokenType.EndObject);
            }

            Expect(ref reader, JsonTokenType.EndObject);

            return value;
        }

        /// <inheritdoc/>
        public override void Write(Utf8JsonWriter writer, Dictionary<TKey, TValue> value, JsonSerializerOptions options)
        {
            writer.WriteStartObject();

            foreach (var entry in value)
            {
                writer.WritePropertyName(entry.Key.ToString());

                writer.WriteStartObject();

                JsonSerializer.Serialize(writer, entry.Value, options);

                writer.WriteEndObject();
            }

            writer.WriteEndObject();
        }
    }
}
