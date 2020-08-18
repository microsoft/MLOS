using System.Collections.Generic;
using System.Runtime.CompilerServices;

namespace Mlos.Core.Collections
{
#pragma warning disable CS0659 // Type overrides Object.Equals(object o) but does not override Object.GetHashCode()
#pragma warning disable CA1066 // Type {0} should implement IEquatable<T> because it overrides Equals
#pragma warning disable CA2231 // Overload operator equals on overriding value type Equals
#pragma warning disable CA1815 // Override equals and operator equals on value types

    /// <summary>
    /// Int32 comparer.
    /// </summary>
    public struct Int32EqualityComparer : IEqualityComparer<int>
    {
        [method: MethodImpl(MethodImplOptions.AggressiveInlining)]
        public bool Equals(int x, int y)
        {
            return x == y;
        }

        [method: MethodImpl(MethodImplOptions.AggressiveInlining)]
        public int GetHashCode(int value)
        {
            return value.GetHashCode();
        }
    }

    /// <summary>
    /// Int64 comparer.
    /// </summary>
    public struct Int64EqualityComparer : IEqualityComparer<long>
    {
        [method: MethodImpl(MethodImplOptions.AggressiveInlining)]
        public bool Equals(long x, long y)
        {
            return x == y;
        }

        [method: MethodImpl(MethodImplOptions.AggressiveInlining)]
        public int GetHashCode(long value)
        {
            return value.GetHashCode();
        }
    }
#pragma warning restore CA1815 // Override equals and operator equals on value types
#pragma warning restore CA2231 // Overload operator equals on overriding value type Equals
#pragma warning restore CA1066 // Type {0} should implement IEquatable<T> because it overrides Equals
#pragma warning restore CS0659 // Type overrides Object.Equals(object o) but does not override Object.GetHashCode()
}
