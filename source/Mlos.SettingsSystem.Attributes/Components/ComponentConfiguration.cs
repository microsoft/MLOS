// -----------------------------------------------------------------------
// <copyright file="ComponentConfiguration.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

namespace Mlos.SettingsSystem.Components
{
    /// <summary>
    /// Component data configuration.
    /// </summary>
    public struct ComponentConfiguration : IEquatable<ComponentConfiguration>
    {
        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(ComponentConfiguration left, ComponentConfiguration right)
        {
            return left.Equals(right);
        }

        /// <summary>
        /// Operator !=.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(ComponentConfiguration left, ComponentConfiguration right)
        {
            return !(left == right);
        }

        /// <inheritdoc />
        public override bool Equals(object obj)
        {
            if (!(obj is ComponentConfiguration))
            {
                return false;
            }

            return Equals((ComponentConfiguration)obj);
        }

        /// <inheritdoc />
        public bool Equals(ComponentConfiguration other)
        {
            return ActiveConfigId == other.ActiveConfigId &&
                SuggestedConfigId == other.SuggestedConfigId;
        }

        /// <inheritdoc />
        public override int GetHashCode()
        {
            return base.GetHashCode();
        }

        /// <summary>
        /// // Set by the component, upon consuming the config.
        /// </summary>
        public ulong ActiveConfigId;

        /// <summary>
        /// Set by the agent upon suggesting new config.
        /// </summary>
        public ulong SuggestedConfigId;
    }
}
