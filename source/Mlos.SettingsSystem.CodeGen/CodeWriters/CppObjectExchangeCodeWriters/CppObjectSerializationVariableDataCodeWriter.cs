// -----------------------------------------------------------------------
// <copyright file="CppObjectSerializationVariableDataCodeWriter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

namespace Mlos.SettingsSystem.CodeGen.CodeWriters.CppObjectExchangeCodeWriters
{
    /// <summary>
    /// Writes cpp type serialization code.
    /// </summary>
    /// <remarks>
    /// Serialization function is using ObjectSerialization::SerializedLength.
    ///
    /// How we serialize:
    ///  serialize whole object flat,
    ///  then serialize the variable length fields, recursively, and keep updating the offset, size where we keep the field.
    /// </remarks>
    internal class CppObjectSerializationVariableDataCodeWriter : CppCodeWriter
    {
        /// <inheritdoc />
        public override bool Accept(Type sourceType)
        {
            // Fixed length structure with no variable length fields.
            // No custom serialization is required.
            //
            CppType cppType = CppTypeMapper.GetCppType(sourceType);
            return cppType.HasVariableData;
        }

        /// <summary>
        /// Write beginning of the file.
        /// </summary>
        /// <remarks>
        /// All serialization methods including the specialized ones are defined in ObjectSerialization namespace.
        /// </remarks>
        public override void WriteBeginFile()
        {
            WriteLine($"namespace {Constants.ObjectSerializationNamespace}");
            WriteLine("{");

            IndentationLevel++;
        }

        /// <inheritdoc />
        public override void WriteEndFile()
        {
            IndentationLevel--;
            WriteLine("};");
            WriteLine();
        }

        /// <summary>
        /// Ignore the type namespace as we are using ObjectSerialization namespace.
        /// </summary>
        /// <param name="namespace"></param>
        public override void WriteOpenTypeNamespace(string @namespace)
        {
            // Nothing.
            //
        }

        /// <inheritdoc />
        public override void WriteCloseTypeNamespace(string @namespace)
        {
            // Nothing.
            //
        }

        /// <summary>
        /// Write a specialization of the serialization function for the provided type.
        /// </summary>
        /// <param name="sourceType"></param>
        public override void BeginVisitType(Type sourceType)
        {
            string cppElementTypeFullName = CppTypeMapper.GenerateCppFullTypeName(sourceType);

            WriteBlock(@$"
                template<>
                inline size_t SerializeVariableData<{cppElementTypeFullName}>(Mlos::Core::BytePtr buffer, uint64_t objectOffset, uint64_t dataOffset, const {cppElementTypeFullName}& object)
                {{
                    size_t totalDataSize = 0;
                    size_t dataSize = 0;");
            WriteLine();

            IndentationLevel++;
        }

        /// <summary>
        /// End of the function, return total variable data size.
        /// </summary>
        /// <param name="sourceType"></param>
        public override void EndVisitType(Type sourceType)
        {
            WriteLine("return totalDataSize;");
            IndentationLevel--;

            WriteLine("};");
            WriteLine();
        }

        /// <inheritdoc />
        /// <summary>
        /// If field has variable length, write serialization code.
        /// </summary>
        /// <param name="cppField"></param>
        public override void VisitField(CppField cppField)
        {
            if (!cppField.CppType.HasVariableData)
            {
                // Ignore field with sized size.
                //
                return;
            }

            // Variable length field.
            //
            WriteBlock($@"
                // Update variable length field : {cppField.FieldInfo.Name} {cppField.CppType.Name}
                //
                dataSize = SerializeVariableData(buffer, objectOffset + {cppField.CppStructOffset}, dataOffset, object.{cppField.FieldInfo.Name});
                totalDataSize += dataSize;
                dataOffset += dataSize;");
            WriteLine();
        }
    }
}
