// -----------------------------------------------------------------------
// <copyright file="OptimizerServiceEncoderDecoder.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using Mlos.Model.Services.Spaces;

namespace Mlos.Model.Services.Client
{
    public static class OptimizerServiceEncoder
    {
        public static OptimizerService.SimpleHypergrid EncodeHypergrid(Hypergrid hypergrid)
        {
            OptimizerService.SimpleHypergrid instance = new OptimizerService.SimpleHypergrid();

            foreach (var subgridSet in hypergrid.Subgrids.Values)
            {
                foreach (var subgrid in subgridSet)
                {
                    instance.GuestSubgrids.Add(EncodeSubgridJoin(subgrid));
                }
            }

            foreach (var dimension in hypergrid.Dimensions)
            {
                instance.Dimensions.Add(EncodeDimension(dimension));
            }

            instance.Name = hypergrid.Name;

            return instance;
        }

        public static OptimizerService.OptimizationProblem EncodeOptimizationProblem(OptimizationProblem problem)
        {
            OptimizerService.OptimizationProblem instance = new OptimizerService.OptimizationProblem();
            instance.ParameterSpace = EncodeHypergrid(problem.ParameterSpace);
            instance.ObjectiveSpace = EncodeHypergrid(problem.ObjectiveSpace);
            foreach (var objective in problem.Objectives)
            {
                instance.Objectives.Add(EncodeObjective(objective));
            }

            if (problem.ContextSpace == null)
            {
                instance.EmptyContext = new OptimizerService.Empty();
            }
            else
            {
                instance.ContextSpace = EncodeHypergrid(problem.ContextSpace);
            }

            return instance;
        }

        public static OptimizerService.Objective EncodeObjective(OptimizationObjective objective)
        {
            return new OptimizerService.Objective
            {
                Minimize = objective.Minimize,
                Name = objective.Name,
            };
        }

        public static OptimizerService.GuestSubgrid EncodeSubgridJoin(SubgridJoin subgridJoin)
        {
            return new OptimizerService.GuestSubgrid
            {
                ExternalPivotDimension = EncodeDimension(subgridJoin.OnExternalJoin),
                Subgrid = EncodeHypergrid(subgridJoin.Subgrid),
            };
        }

        private static OptimizerService.DimensionType DimensionToGrpcType(DimensionTypeName typeName)
        {
            switch (typeName)
            {
                case DimensionTypeName.CategoricalDimension:
                    return OptimizerService.DimensionType.Categorical;
                case DimensionTypeName.ContinuousDimension:
                    return OptimizerService.DimensionType.Continuous;
                case DimensionTypeName.DiscreteDimension:
                    return OptimizerService.DimensionType.Discrete;
                case DimensionTypeName.OrdinalDimension:
                    return OptimizerService.DimensionType.Ordinal;
                default:
                    throw new System.ArgumentException("Invalid type provided to OptimizerServiceEncoderDecoder.Encoder.DimensionToGrpcType(..). Type: " + typeName);
            }
        }

        public static OptimizerService.Dimension EncodeDimension(IDimension dimension)
        {
            // C# Syntax equivalent to
            // if(dimension is EmptyDimension) {
            //      var emptyDimension = (EmptyDimension) dimension; ..
            // }
            if (dimension is EmptyDimension emptyDimension)
            {
                return new OptimizerService.Dimension
                {
                    EmptyDimension = EncodeEmptyDimension(emptyDimension),
                };
            }
            else if (dimension is ContinuousDimension continuousDimension)
            {
                return new OptimizerService.Dimension
                {
                    ContinuousDimension = EncodeContinuousDimension(continuousDimension),
                };
            }
            else if (dimension is DiscreteDimension discreteDimension)
            {
                return new OptimizerService.Dimension
                {
                    DiscreteDimension = EncodeDiscreteDimension(discreteDimension),
                };
            }
            else if (dimension is OrdinalDimension ordinalDimension)
            {
                return new OptimizerService.Dimension
                {
                    OrdinalDimension = EncodeOrdinalDimension(ordinalDimension),
                };
            }
            else if (dimension is CategoricalDimension categoricalDimension)
            {
                return new OptimizerService.Dimension
                {
                    CategoricalDimension = EncodeCategoricalDimension(categoricalDimension),
                };
            }
            else if (dimension is CompositeDimension compositeDimension)
            {
                return new OptimizerService.Dimension
                {
                    CompositeDimension = EncodeCompositeDimension(compositeDimension),
                };
            }
            else
            {
                throw new System.ArgumentException("Invalid dimension type provided to OptimizerServiceEncoderDecoder.Encoder.EncodeDimension(..). Type: " + dimension.GetType());
            }
        }

        public static OptimizerService.CompositeDimension EncodeCompositeDimension(CompositeDimension dimension)
        {
            OptimizerService.Dimension[] chunks = new OptimizerService.Dimension[dimension.Values.Count];
            var i = 0;
            foreach (var chunk in dimension.Values)
            {
                chunks[i++] = EncodeDimension(chunk);
            }

            return new OptimizerService.CompositeDimension
            {
                Name = dimension.Name,
                ChunkType = DimensionToGrpcType(dimension.ChunkType),
                Chunks = { chunks },
            };
        }

        public static OptimizerService.DiscreteDimension EncodeDiscreteDimension(DiscreteDimension dimension)
        {
            return new OptimizerService.DiscreteDimension
            {
                Name = dimension.Name,
                Min = dimension.Min,
                Max = dimension.Max,
            };
        }

        public static OptimizerService.EmptyDimension EncodeEmptyDimension(EmptyDimension dimension)
        {
            return new OptimizerService.EmptyDimension
            {
                Name = dimension.Name,
                DimensionType = DimensionToGrpcType(dimension.ObjectType),
            };
        }

        public static OptimizerService.ContinuousDimension EncodeContinuousDimension(ContinuousDimension dimension)
        {
            return new OptimizerService.ContinuousDimension
            {
                Name = dimension.Name,
                Min = dimension.Min,
                Max = dimension.Max,
                IncludeMin = dimension.IncludeMin,
                IncludeMax = dimension.IncludeMax,
            };
        }

        public static OptimizerService.OrdinalDimension EncodeOrdinalDimension(OrdinalDimension dimension)
        {
            var instance = new OptimizerService.OrdinalDimension();
            instance.Name = dimension.Name;
            instance.Ascending = dimension.Ascending;
            foreach (var value in dimension.OrderedValues)
            {
                instance.OrderedValues.Add(EncodePrimitiveValue(value));
            }

            return instance;
        }

        public static OptimizerService.CategoricalDimension EncodeCategoricalDimension(CategoricalDimension dimension)
        {
            var instance = new OptimizerService.CategoricalDimension();
            instance.Name = dimension.Name;
            foreach (var value in dimension.Values)
            {
                instance.Values.Add(EncodePrimitiveValue(value));
            }

            return instance;
        }

        public static OptimizerService.PrimitiveValue EncodePrimitiveValue(object value)
        {
            var data = new OptimizerService.PrimitiveValue();
            if (value is int)
            {
                data.IntValue = (int)value;
            }
            else if (value is bool)
            {
                data.BoolValue = (bool)value;
            }
            else if (value is string)
            {
                data.StringValue = (string)value;
            }
            else if (value is double)
            {
                data.DoubleValue = (double)value;
            }
            else
            {
                throw new System.ArgumentException("Invalid type provided to OptimizerServiceEncoderDecoder.Encoder.EncodePrimitiveValue(..). Type: " + value.GetType());
            }

            return data;
        }
    }

    public static class OptimizerServiceDecoder
    {
        private static DimensionTypeName GrpcTypeToDimension(OptimizerService.DimensionType typeName)
        {
            switch (typeName)
            {
                case OptimizerService.DimensionType.Categorical:
                    return DimensionTypeName.CategoricalDimension;
                case OptimizerService.DimensionType.Continuous:
                    return DimensionTypeName.ContinuousDimension;
                case OptimizerService.DimensionType.Ordinal:
                    return DimensionTypeName.OrdinalDimension;
                case OptimizerService.DimensionType.Discrete:
                    return DimensionTypeName.DiscreteDimension;
                default:
                    throw new System.ArgumentException("Invalid type provided to OptimizerServiceEncoderDecoder.Decoder.GrpcTypeToDimension(..). Type: " + typeName);
            }
        }

        public static OptimizationProblem DecodeOptimizationProblem(OptimizerService.OptimizationProblem problem)
        {
            var objectives = new OptimizationObjective[problem.Objectives.Count];
            var i = 0;
            foreach (var objective in problem.Objectives)
            {
                objectives[i++] = DecodeOptimizationObjective(objective);
            }

            var instance = new OptimizationProblem(
                        DecodeHypergrid(problem.ParameterSpace),
                        DecodeHypergrid(problem.ObjectiveSpace),
                        objectives);
            if (problem.ContextOptionsCase == OptimizerService.OptimizationProblem.ContextOptionsOneofCase.ContextSpace)
            {
                // A context space was provided
                instance.ContextSpace = DecodeHypergrid(problem.ContextSpace);
            }

            return instance;
        }

        public static OptimizationObjective DecodeOptimizationObjective(OptimizerService.Objective objective)
        {
            return new OptimizationObjective(objective.Name, objective.Minimize);
        }

        public static EmptyDimension DecodeEmptyDimension(OptimizerService.EmptyDimension dimension)
        {
            return new EmptyDimension(dimension.Name, GrpcTypeToDimension(dimension.DimensionType));
        }

        public static DiscreteDimension DecodeDiscreteDimension(OptimizerService.DiscreteDimension dimension)
        {
            return new DiscreteDimension(dimension.Name, dimension.Min, dimension.Max);
        }

        public static CategoricalDimension DecodeCategoricalDimension(OptimizerService.CategoricalDimension dimension)
        {
            var values = new object[dimension.Values.Count];
            var i = 0;
            foreach (var value in dimension.Values)
            {
                values[i++] = DecodePrimitiveValue(value);
            }

            return new CategoricalDimension(dimension.Name, values);
        }

        public static IDimension DecodeDimension(OptimizerService.Dimension dimension)
        {
            switch (dimension.DimensionCase)
            {
                case OptimizerService.Dimension.DimensionOneofCase.ContinuousDimension:
                    return DecodeContinuousDimension(dimension.ContinuousDimension);
                case OptimizerService.Dimension.DimensionOneofCase.DiscreteDimension:
                    return DecodeDiscreteDimension(dimension.DiscreteDimension);
                case OptimizerService.Dimension.DimensionOneofCase.OrdinalDimension:
                    return DecodeOrdinalDimension(dimension.OrdinalDimension);
                case OptimizerService.Dimension.DimensionOneofCase.CategoricalDimension:
                    return DecodeCategoricalDimension(dimension.CategoricalDimension);
                case OptimizerService.Dimension.DimensionOneofCase.CompositeDimension:
                    return DecodeCompositeDimension(dimension.CompositeDimension);
                case OptimizerService.Dimension.DimensionOneofCase.EmptyDimension:
                    return DecodeEmptyDimension(dimension.EmptyDimension);
                default:
                    throw new System.ArgumentException("Invalid type provided to OptimizerServiceEncoderDecoder.Decoder.DecodeDimension(..). Type: " + dimension.GetType());
            }
        }

        public static CompositeDimension DecodeCompositeDimension(OptimizerService.CompositeDimension dimension)
        {
            var chunks = new IDimension[dimension.Chunks.Count];
            var i = 0;
            foreach (var serialized_chunk in dimension.Chunks)
            {
                chunks[i++] = DecodeDimension(serialized_chunk);
            }

            return new CompositeDimension(dimension.Name, GrpcTypeToDimension(dimension.ChunkType), chunks);
        }

        public static Hypergrid DecodeHypergrid(OptimizerService.SimpleHypergrid hypergrid)
        {
            var dimensions = new IDimension[hypergrid.Dimensions.Count];
            var i = 0;
            foreach (var dimension in hypergrid.Dimensions)
            {
                dimensions[i++] = DecodeDimension(dimension);
            }

            var instance = new Hypergrid(hypergrid.Name, dimensions);
            foreach (var subgrid in hypergrid.GuestSubgrids)
            {
                instance.Join(DecodeHypergrid(subgrid.Subgrid), DecodeDimension(subgrid.ExternalPivotDimension));
            }

            return instance;
        }

        public static SubgridJoin DecodeSubgridJoin(OptimizerService.GuestSubgrid subgrid)
        {
            return new SubgridJoin
            {
                Subgrid = DecodeHypergrid(subgrid.Subgrid),
                OnExternalJoin = DecodeDimension(subgrid.ExternalPivotDimension),
            };
        }

        public static ContinuousDimension DecodeContinuousDimension(OptimizerService.ContinuousDimension dimension)
        {
            return new ContinuousDimension(dimension.Name, dimension.Min, dimension.Max, dimension.IncludeMin, dimension.IncludeMax);
        }

        public static OrdinalDimension DecodeOrdinalDimension(OptimizerService.OrdinalDimension dimension)
        {
            var values = new object[dimension.OrderedValues.Count];
            var i = 0;
            foreach (var value in dimension.OrderedValues)
            {
                values[i++] = DecodePrimitiveValue(value);
            }

            return new OrdinalDimension(dimension.Name, dimension.Ascending, values);
        }

        public static object DecodePrimitiveValue(OptimizerService.PrimitiveValue value)
        {
            switch (value.ValueCase)
            {
                case OptimizerService.PrimitiveValue.ValueOneofCase.IntValue:
                    return (int)value.IntValue;
                case OptimizerService.PrimitiveValue.ValueOneofCase.DoubleValue:
                    return (double)value.DoubleValue;
                case OptimizerService.PrimitiveValue.ValueOneofCase.BoolValue:
                    return (bool)value.BoolValue;
                case OptimizerService.PrimitiveValue.ValueOneofCase.StringValue:
                    return (string)value.StringValue;
                default:
                    throw new System.ArgumentException("Invalid type provided to OptimizerServiceEncoderDecoder.Decoder.DecodePrimitiveValue(..). Type: " + value.GetType());
            }
        }
    }
}
