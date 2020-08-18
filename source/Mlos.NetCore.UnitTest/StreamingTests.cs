// -----------------------------------------------------------------------
// <copyright file="StreamingTests.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System.Collections.Generic;
using System.Linq;

using Mlos.Streaming;

using Xunit;

namespace Mlos.NetCore.UnitTest
{
    public class StreamingTests
    {
        [Fact]
        public void MinOnBuffer()
        {
            var collection = Enumerable.Range(0, 100);

            var collectionStream = new StreamableSource<int>();

            var results = new List<int>();

            // #TODO, build expression tree and optimize
            // Expression<Action<Streamable<int>>> expression = collectionStream =>
            //

            // Build a pipeline from the collection stream.
            //
            collectionStream
                .Buffer(5)
                .Min()
                .Consume(r =>
                    results.Add(r));

            collectionStream.Publish(collection);

            var expected = Enumerable.Range(0, 20).Select(r => r * 5);

            // #TODO obtain results from the collectionStream
            //
            collectionStream.Inspect();

            Assert.Equal(expected, results);
        }

        [Fact]
        public void CardinalityOfStream()
        {
            var collection = Enumerable.Range(0, 1000);

            var collectionStream = new StreamableSource<int>();

            var results = new List<int>();

            // #TODO, build expression tree and optimize
            // Expression<Action<Streamable<int>>> expression = collectionStream =>
            //

            // Build a pipeline from the collection stream.
            //
            collectionStream
                .CardinalityEstimate(_ => _, 0.1);

            collectionStream.Publish(collection);

            // var expected = Enumerable.Range(0, 20).Select(r => r * 5);

            // #TODO obtain results from the collectionStream
            //
            collectionStream.Inspect();

            // Assert.Equal(expected, results);
        }
    }
}
