// -----------------------------------------------------------------------
// <copyright file="SharedConfig.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Runtime.InteropServices;

using Mlos.SettingsSystem.Attributes;
using Mlos.SettingsSystem.StdTypes;

namespace Mlos.Core
{
    #region Shareable config structures

    /// <summary>
    /// Header of the shared configuration.
    /// </summary>
    /// <remarks>
    /// Shared configuration consist of SharedConfigHeader and two copies of the component configuration.
    /// Explicitly set structure size to be 32.
    /// </remarks>
    [CodegenType]
    [StructLayout(LayoutKind.Sequential, Size = SharedConfigHeader.TypeSize)]
    public partial struct SharedConfigHeader : IEquatable<SharedConfigHeader>
    {
        /// <summary>
        /// Size of the structure.
        /// </summary>
        public const int TypeSize = 32;

        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(SharedConfigHeader left, SharedConfigHeader right) => left.Equals(right);

        /// <summary>
        /// Operator !=.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(SharedConfigHeader left, SharedConfigHeader right) => !(left == right);

        /// <inheritdoc/>
        public override bool Equals(object obj)
        {
            if (!(obj is SharedConfigHeader))
            {
                return false;
            }

            return Equals((SharedConfigHeader)obj);
        }

        /// <inheritdoc/>
        public bool Equals(SharedConfigHeader other) =>
            CodegenTypeIndex == other.CodegenTypeIndex &&
            ConfigId == other.ConfigId;

        /// <inheritdoc/>
        public override int GetHashCode() => base.GetHashCode();

        /// <summary>
        /// Component CodegenType Index.
        /// </summary>
        public uint CodegenTypeIndex;

        /// #TODO that should be part of the config
        /// <summary>
        /// Identifier of the current config.
        /// </summary>
        public AtomicUInt32 ConfigId;
    }
    #endregion

    #region Messages

    /// <summary>
    /// The feedback message is sent from the agent to the target process after the shared config has been updated.
    /// </summary>
    [CodegenMessage]
    public partial struct SharedConfigUpdatedFeedbackMessage : IEquatable<SharedConfigUpdatedFeedbackMessage>
    {
        // #TODO include config primary key

        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(SharedConfigUpdatedFeedbackMessage left, SharedConfigUpdatedFeedbackMessage right) => left.Equals(right);

        /// <summary>
        /// Operator !=.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(SharedConfigUpdatedFeedbackMessage left, SharedConfigUpdatedFeedbackMessage right) => !(left == right);

        /// <inheritdoc />
        public override bool Equals(object obj)
        {
            if (!(obj is StringPtr))
            {
                return false;
            }

            return Equals((StringPtr)obj);
        }

        /// <inheritdoc />
        public bool Equals(SharedConfigUpdatedFeedbackMessage other) => true;

        /// <inheritdoc />
        public override int GetHashCode() => 0;
    }
    #endregion
}
