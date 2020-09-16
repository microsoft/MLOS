// -----------------------------------------------------------------------
// <copyright file="JsonConverterWithExpectations.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Mlos.Model.Services.Spaces.JsonConverters
{
    /// <summary>
    /// The various Expect(...) methods in this class are an attempt at reducing boiler-plate code in
    /// derived classes.
    /// </summary>
    /// <typeparam name="T">.</typeparam>
    public abstract class JsonConverterWithExpectations<T> : JsonConverter<T>
    {
        protected void Expect(ref Utf8JsonReader reader, JsonTokenType expectedTokenType)
        {
            if (!reader.Read())
            {
                throw new JsonException();
            }

            if (reader.TokenType != expectedTokenType)
            {
                throw new JsonException();
            }
        }

        protected void Expect(ref Utf8JsonReader reader, JsonTokenType expectedTokenType, object expectedTokenValue)
        {
            Expect(ref reader, expectedTokenType);

            switch (expectedTokenType)
            {
                case JsonTokenType.PropertyName:
                case JsonTokenType.String:
                    if (reader.GetString() != (string)expectedTokenValue)
                    {
                        throw new JsonException();
                    }

                    break;
                default:
                    throw new JsonException();
            }
        }

        protected void ExpectAny(ref Utf8JsonReader reader, ISet<JsonTokenType> expectedTokenTypes)
        {
            if (!reader.Read())
            {
                throw new JsonException();
            }

            if (!expectedTokenTypes.Contains(reader.TokenType))
            {
                throw new JsonException();
            }
        }

        protected void ExpectBoolean(ref Utf8JsonReader reader)
        {
            if (!reader.Read())
            {
                throw new JsonException();
            }

            if ((reader.TokenType != JsonTokenType.True) && (reader.TokenType == JsonTokenType.False))
            {
                throw new JsonException();
            }
        }

        /// <summary>
        /// Peeks at the next JsonTokenType without affecting the state of the reader.
        ///
        /// Note: the reader is a struct and is not passed by reference. Thus we get a copy
        /// here and are not affecting the state of the reader in the caller.
        /// </summary>
        /// <param name="reader"></param>
        /// <returns></returns>
        protected JsonTokenType PeekNextTokenType(Utf8JsonReader reader)
        {
            if (!reader.Read())
            {
                throw new JsonException();
            }

            return reader.TokenType;
        }
    }
}
