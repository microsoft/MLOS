// -----------------------------------------------------------------------
// <copyright file="TypeCodeGenerator.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;

using Microsoft.CodeAnalysis;

using Mlos.SettingsSystem.Attributes;
using Mlos.SettingsSystem.CodeGen.CodeWriters;

namespace Mlos.SettingsSystem.CodeGen
{
    internal class TypeCodeGenerator
    {
        internal CodeWriter CodeWriter { get; set; }
        internal Compilation SourceCompilation { get; set; }
        internal CodeCommentsReader SourceCodeComments { get; set; }
        internal List<CodegenError> CodeGenErrors { get; set; }

        private void AddUnsupportedFieldTypeError(Type sourceType, FieldInfo fieldInfo) => this.CodeGenErrors.Add(new CodegenError
        {
            ErrorNumber = "Not supported type",
            ErrorText = $"Unsupported field type of class '{sourceType.ToString()}'",
            IsWarning = false,
            FileLinePosition = SourceCompilation.GetFileLinePosition(fieldInfo),
        });

        private void AddUntaggedOrNoneScalarPublicSettingRegistryField(Type sourceType, FieldInfo fieldInfo) => this.CodeGenErrors.Add(new CodegenError
        {
            ErrorNumber = "Untagged or non-scalar public SettingRegistry field",
            ErrorText = $"Public field '{fieldInfo.Name}' in SettingsRegistry type '{sourceType.FullName}' is not a scalar or not tagged as an Mlos code gened field.",
            IsWarning = false,
            FileLinePosition = SourceCompilation.GetFileLinePosition(fieldInfo),
        });

        private void AddInvalidAlignmentSizeError(Type sourceType, FieldInfo fieldInfo) => this.CodeGenErrors.Add(new CodegenError
        {
            ErrorNumber = "Invalid alignment size",
            ErrorText = "Alignment size is required to be a power of 2.",
            IsWarning = false,
            FileLinePosition = SourceCompilation.GetFileLinePosition(fieldInfo),
        });

        private void AddMissingFieldReadonlyModifierError(Type sourceType, FieldInfo fieldInfo) => this.CodeGenErrors.Add(new CodegenError
        {
            ErrorNumber = "Missing field readonly modifier",
            ErrorText = $"Fixed size array field {fieldInfo.Name} of class '{sourceType.ToString()}' should be readonly",
            IsWarning = false,
            FileLinePosition = SourceCompilation.GetFileLinePosition(fieldInfo),
        });

        private void AddIncorrectDefinitionError(Type sourceType, FieldInfo fieldInfo) => this.CodeGenErrors.Add(new CodegenError
        {
            ErrorNumber = "Incorrect definition",
            ErrorText = $"FixedArray can be only used in class '{sourceType}'",
            IsWarning = false,
            FileLinePosition = SourceCompilation.GetFileLinePosition(fieldInfo),
        });

        /// <summary>
        /// Generate the necessary code for a given type.
        /// </summary>
        /// <param name="sourceType"></param>
        /// <returns>True if there were no codegen errors.</returns>
        public bool GenerateType(Type sourceType)
        {
            if (CppTypeMapper.HasCppType(sourceType))
            {
                // We already generated a Cpp type.
                //
                return true;
            }

            CppTypeMapper.DeclareType(sourceType);

            GenerateSubTypes(sourceType, out bool hasVariableSerializableLength);

            // Failed to generate required field types.
            //
            if (CodeGenErrors.Any())
            {
                return false;
            }

            DefineCppType(sourceType, hasVariableSerializableLength, out List<CppField> cppFields);

            // We are unable to generate code, return early.
            //
            if (CodeGenErrors.Any())
            {
                return false;
            }

            if (CodeWriter.Accept(sourceType))
            {
                WriteCode(sourceType, cppFields);
            }

            return true;
        }

        private void DefineCppType(Type sourceType, bool hasVariableSerializableLength, out List<CppField> cppFields)
        {
            cppFields = new List<CppField>();

            // Build list of structure properties.
            // Calculate fields offsets for flatten structure.
            //
            uint cppStructOffset = 0;

            // Calculate the type aligment, this is required when type is used as inner type in other types.
            //
            uint alignment = 1;

            // Export public instance fields.
            //
            foreach (FieldInfo fieldInfo in sourceType.GetPublicInstanceFields())
            {
                if (sourceType.IsCodegenConfigType() && !fieldInfo.IsScalarSetting())
                {
                    AddUntaggedOrNoneScalarPublicSettingRegistryField(sourceType, fieldInfo);
                    continue;
                }

                if (!IsSupportedFieldType(fieldInfo, out CppType cppFieldType))
                {
                    AddUnsupportedFieldTypeError(sourceType, fieldInfo);
                    continue;
                }

                if (!IsValidAlignmentSizeAttribute(fieldInfo, out uint customFieldAlignment))
                {
                    AddInvalidAlignmentSizeError(sourceType, fieldInfo);
                    continue;
                }

                // Align the field offset and update type aligment.
                //
                uint fieldAlignment = customFieldAlignment == 0
                    ? cppFieldType.Alignment
                    : customFieldAlignment;

                if (fieldAlignment != 0)
                {
                    cppStructOffset = CppTypeMapper.AlignSize(cppStructOffset, fieldAlignment);

                    alignment = Math.Max(alignment, fieldAlignment);
                }

                // Calculate type size.
                //
                uint typeSize = cppFieldType.TypeSize;

                // Calculate field size in case when we have an array.
                //
                if (fieldInfo.IsFixedSizedArray())
                {
                    if (!fieldInfo.IsInitOnly)
                    {
                        AddMissingFieldReadonlyModifierError(sourceType, fieldInfo);
                    }

                    if (!sourceType.IsClass)
                    {
                        AddIncorrectDefinitionError(sourceType, fieldInfo);
                    }

                    FixedSizeArrayAttribute arrayAttribute = fieldInfo.GetCustomAttribute<FixedSizeArrayAttribute>();

                    // Adjust the structure size.
                    //
                    typeSize += typeSize * (arrayAttribute.Length - 1);
                }

                cppFields.Add(
                    new CppField
                    {
                        CppStructOffset = cppStructOffset,
                        FieldInfo = fieldInfo,
                        CppType = cppFieldType,
                    });

                cppStructOffset += typeSize;
            }

            if (CodeGenErrors.Any())
            {
                // We are unable to generate code, return early.
                //
                return;
            }

            uint paddingSize = 0;

            // Align structure size unless it has explicitly defined size.
            //
            if (sourceType.StructLayoutAttribute.Size == 0)
            {
                cppStructOffset = CppTypeMapper.AlignSize(cppStructOffset, alignment);
            }
            else
            {
                // Explicity defined size, calculate padding.
                //
                paddingSize = (uint)sourceType.StructLayoutAttribute.Size - cppStructOffset;
                cppStructOffset += paddingSize;
            }

            // Check the final structure aligment.
            //
            AlignAttribute alignmentAttribute = sourceType.GetCustomAttribute<AlignAttribute>();

            if (alignmentAttribute != null)
            {
                alignment = alignmentAttribute.Size;
            }

            // Define a new Cpp type.
            //
            CppTypeMapper.DefineType(
                sourceType,
                cppTypeSize: cppStructOffset,
                aligment: alignment,
                paddingSize: paddingSize,
                hasVariableSerializableLength: hasVariableSerializableLength);
        }

        private void GenerateSubTypes(Type sourceType, out bool hasVariableSerializableLength)
        {
            hasVariableSerializableLength = false;

            // Check do we have all cpp types required to generate a type.
            //
            foreach (FieldInfo fieldInfo in sourceType.GetPublicInstanceFields())
            {
                if (fieldInfo.IsString())
                {
                    // Structure contains a string field.
                    //
                    hasVariableSerializableLength = true;
                }

                // For arrays, ensure the array element type has been generated.
                //
                Type fieldType = fieldInfo.IsFixedSizedArray() ? fieldInfo.FieldType.GetElementType() : fieldInfo.FieldType;

                if (CppTypeMapper.TryGetCppType(fieldType, out CppType cppType))
                {
                    // Cpp type has been generated, safe to use.
                    //
                    if (cppType.HasVariableData)
                    {
                        // Field type is variable length, so containing structure is also variable length.
                        //
                        hasVariableSerializableLength = true;
                    }

                    continue;
                }

                // Recursively generate field type.
                //
                if (!this.GenerateType(fieldType))
                {
                    // There are errors, however continue, so we can report on all of them in one shot.
                    //
                }
            }
        }

        private void WriteCode(Type sourceType, List<CppField> cppFields)
        {
            // Open Namespace.
            //
            CodeWriter.WriteOpenTypeNamespace(sourceType.Namespace);

            // Class comment.
            //
            CodeComment? codeComment = SourceCodeComments.GetCodeComment(sourceType);
            if (codeComment.HasValue)
            {
                CodeWriter.WriteComments(codeComment.Value);
            }

            // Class definition.
            //
            CodeWriter.BeginVisitType(sourceType);

            // Fields definition.
            //
            foreach (CppField cppField in cppFields)
            {
                // Write a field comment.
                //
                if (codeComment.HasValue)
                {
                    codeComment = SourceCodeComments.GetCodeComment(cppField.FieldInfo);
                    if (codeComment.HasValue)
                    {
                        CodeWriter.WriteComments(codeComment.Value);
                    }
                }

                // Write a field definition.
                //
                CodeWriter.VisitField(cppField);
            }

            // Class end.
            //
            CodeWriter.EndVisitType(sourceType);

            // Close namespace.
            //
            CodeWriter.WriteCloseTypeNamespace(sourceType.Namespace);
        }

        private bool IsPowerOfTwo(ulong num)
        {
            return num != 0 && ((num & (num - 1)) == 0);
        }

        private bool IsSupportedFieldType(FieldInfo fieldInfo, out CppType cppFieldType)
        {
            Type fieldType = fieldInfo.IsFixedSizedArray() ? fieldInfo.FieldType.GetElementType() : fieldInfo.FieldType;

            return CppTypeMapper.TryGetCppType(fieldType, out cppFieldType);
        }

        private bool IsValidAlignmentSizeAttribute(FieldInfo fieldInfo, out uint alignment)
        {
            alignment = 0;
            AlignAttribute alignmentSizeAttribute = fieldInfo.GetCustomAttribute<AlignAttribute>();
            if (alignmentSizeAttribute == null)
            {
                return true;
            }

            bool isValid = IsPowerOfTwo(alignmentSizeAttribute.Size);
            if (isValid)
            {
                alignment = alignmentSizeAttribute.Size;
            }

            return isValid;
        }
    }

    /// <summary>
    /// Describes the code gen error.
    /// </summary>
    internal struct CodegenError
    {
        internal string ErrorNumber { get; set; }
        internal string ErrorText { get; set; }
        internal bool IsWarning { get; set; }
        internal FileLinePositionSpan FileLinePosition { get; set; }
    }
}
