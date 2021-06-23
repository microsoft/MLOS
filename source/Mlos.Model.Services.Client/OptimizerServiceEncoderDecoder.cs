// -----------------------------------------------------------------------
// <copyright file="OptimizerServiceEncoderDecoder.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System.Linq;

using Mlos.Model.Services.Spaces;

namespace Mlos.Model.Services.Client
{
    public static class OptimizerServiceEncoder
    {
        public static OptimizerService.SimpleHypergrid EncodeHypergrid(Hypergrid hypergrid)
        {
            OptimizerService.SimpleHypergrid instance = new OptimizerService.SimpleHypergrid();

            instance.GuestSubgrids.AddRange(hypergrid.Subgrids.SelectMany(subgridSet => subgridSet.Value.Select(subgrid => EncodeJoinedSubgrid(subgrid))));

            instance.Dimensions.AddRange(hypergrid.Dimensions.Select(dimension => EncodeDimension(dimension)));

            instance.Name = hypergrid.Name;

            return instance;
        }

        public static OptimizerService.OptimizationProblem EncodeOptimizationProblem(OptimizationProblem problem)
        {
            OptimizerService.OptimizationProblem instance = new OptimizerService.OptimizationProblem();
            instance.ParameterSpace = EncodeHypergrid(problem.ParameterSpace);
            instance.ObjectiveSpace = EncodeHypergrid(problem.ObjectiveSpace);
            instance.Objectives.AddRange(
                problem.Objectives.Select(objective => EncodeObjective(objective)));
            instance.ContextSpace = problem.ContextSpace == null ? null : EncodeHypergrid(problem.ContextSpace);

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

        public static OptimizerService.GuestSubgrid EncodeJoinedSubgrid(JoinedSubgrid joinedSubgrid)
        {
            return new OptimizerService.GuestSubgrid
            {
                ExternalPivotDimension = EncodeDimension(joinedSubgrid.OnExternalJoin),
                Subgrid = EncodeHypergrid(joinedSubgrid.Subgrid),
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
            var instance = new OptimizerService.CompositeDimension
            {
                Name = dimension.Name,
                ChunkType = DimensionToGrpcType(dimension.ChunkType),
            };

            instance.Chunks.AddRange(dimension.Values.Select(chunk => EncodeDimension(chunk)));
            return instance;
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
            instance.OrderedValues.AddRange(
                dimension.OrderedValues.Select(value => EncodePrimitiveValue(value)));

            return instance;
        }

        public static OptimizerService.CategoricalDimension EncodeCategoricalDimension(CategoricalDimension dimension)
        {
            var instance = new OptimizerService.CategoricalDimension();
            instance.Name = dimension.Name;
            instance.Values.AddRange(dimension.Values.Select(value => EncodePrimitiveValue(value)));

            return instance;
        }

        public static OptimizerService.PrimitiveValue EncodePrimitiveValue(object value)
        {
            var data = new OptimizerService.PrimitiveValue();
            if (value is int intValue)
            {
                data.IntValue = intValue;
            }
            else if (value is bool boolValue)
            {
                data.BoolValue = boolValue;
            }
            else if (value is string stringValue)
            {
                data.StringValue = stringValue;
            }
            else if (value is double doubleValue)
            {
                data.DoubleValue = doubleValue;
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
            var objectives = problem.Objectives.Select(objective => DecodeOptimizationObjective(objective)).ToList();

            var instance = new OptimizationProblem(
                parameterSpace: DecodeHypergrid(problem.ParameterSpace),
                objectiveSpace: DecodeHypergrid(problem.ObjectiveSpace),
                objectives: objectives);
            if (problem.ContextSpace != null)
            {
                // A context space was provided.
                //
                instance.ContextSpace = DecodeHypergrid(problem.ContextSpace);
            }
            else
            {
                instance.ContextSpace = null;
            }

            return instance;
        }

        public static OptimizationObjective DecodeOptimizationObjective(OptimizerService.Objective objective)
        {
            return new OptimizationObjective(name: objective.Name, minimize: objective.Minimize);
        }

        public static EmptyDimension DecodeEmptyDimension(OptimizerService.EmptyDimension dimension)
        {
            return new EmptyDimension(name: dimension.Name, dataType: GrpcTypeToDimension(dimension.DimensionType));
        }

        public static DiscreteDimension DecodeDiscreteDimension(OptimizerService.DiscreteDimension dimension)
        {
            return new DiscreteDimension(name: dimension.Name, min: dimension.Min, max: dimension.Max);
        }

        public static CategoricalDimension DecodeCategoricalDimension(OptimizerService.CategoricalDimension dimension)
        {
            object[] values = dimension.Values.Select(value => DecodePrimitiveValue(value)).ToArray();
            return new CategoricalDimension(name: dimension.Name, values: values);
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
            IDimension[] chunks = dimension.Chunks.Select(serialized_chunk => DecodeDimension(serialized_chunk)).ToArray();
            return new CompositeDimension(name: dimension.Name, chunkType: GrpcTypeToDimension(dimension.ChunkType), chunks);
        }

        public static Hypergrid DecodeHypergrid(OptimizerService.SimpleHypergrid hypergrid)
        {
            IDimension[] dimensions = hypergrid.Dimensions.Select(dimension => DecodeDimension(dimension)).ToArray();

            var instance = new Hypergrid(name: hypergrid.Name, dimensions: dimensions);
            foreach (var subgrid in hypergrid.GuestSubgrids)
            {
                instance.Join(DecodeHypergrid(subgrid.Subgrid), DecodeDimension(subgrid.ExternalPivotDimension));
            }

            return instance;
        }

        public static JoinedSubgrid DecodeJoinedSubgrid(OptimizerService.GuestSubgrid subgrid)
        {
            return new JoinedSubgrid
            {
                Subgrid = DecodeHypergrid(subgrid.Subgrid),
                OnExternalJoin = DecodeDimension(subgrid.ExternalPivotDimension),
            };
        }

        public static ContinuousDimension DecodeContinuousDimension(OptimizerService.ContinuousDimension dimension)
        {
            return new ContinuousDimension(
                name: dimension.Name,
                min: dimension.Min,
                max: dimension.Max,
                includeMin: dimension.IncludeMin,
                includeMax: dimension.IncludeMax);
        }

        public static OrdinalDimension DecodeOrdinalDimension(OptimizerService.OrdinalDimension dimension)
        {
            object[] values = dimension.OrderedValues.Select(value => DecodePrimitiveValue(value)).ToArray();

            return new OrdinalDimension(name: dimension.Name, ascending: dimension.Ascending, orderedValues: values);
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
