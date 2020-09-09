#CodeGen

# Intro

Document describes internal _CodeGen_ implementation.

# MLOS goals

Provide an ability to expose internal application settings, telemetry, and events to an external agent.
Codegen responsibility is to generate a set of classes and helper methods to exchange the messages and share (read and update) config structures residing in the shared memory.

## Why custom CodeGen?
Not [Protocol Buffers](https://developers.google.com/protocol-buffers), [FlatBuffers](https://google.github.io/flatbuffers/), XEvents etc...

The answer is performance and full control. Emitting the telemetry will occur on the hot path (_not always_).
We must make sure that we keep code sending the telemetry short and fast as possible. On SKUs with small CPU count, the telemetry code will extend the critical path.
The ability to recover the application depends (_among others_) on the exchange framework.

### Performance

Interesting benchmarks can be found here [bitsery](https://github.com/fraillt/cpp_serializers_benchmark)


|data size | serialize |deserialize|
|----------|-----------|-----------|
|bitsery|6913B|1252ms|1170ms|
|bitsery_compress|4213B|1445ms|1325ms|
|boost|11037B|9952ms|8767ms|
|cereal|10413B|6497ms|5470ms|
|flatbuffers|14924B|6762ms|2173ms|
|yas|10463B|1352ms|1109ms|
|yas_compress|7315B|1673ms|1598ms|

### Then why not XEvents ?

XEvents generates code responsible for emitting the telemetry; CodeGen creates both sender and the receiver side. CodeGen creates additional code required for shared config lookups.

### Benefits
- full control over the code, no external dependenices
- clean and simple implementation, we are using C# type system (class definitions and attributes),
  that leads to simple and clean code
- simple, extensible architecture
  to add new language support, just add CodeWriters (for example Python Cpp bindings).
- easy to integrate with SqlServer (no Cpp standard or open source libraries incompatible with SOS memory management and error handling)
- easy to open source (no proprietary dependenices)

## Build process

Codegen works on the types definied in C# assembly. This assembly is called *SettingsRegistry*. The project definition has a group of files that are included in the code generation workflow.

```csproj
<ItemGroup Label="SettingsRegistryDefs">
  <SettingsRegistryDef Include="Codegen\AssemblyInfo.cs" />
  <SettingsRegistryDef Include="Codegen\SharedChannelConfig.cs" />
</ItemGroup>
```

First codegen compiles files marked as SettingsRegistryDef to temporary assembly.
From this assembly codegen using reflection discovers all the types that are marked as code gen and process the types though the chain of code gen classes.

As results codegen produces files. We can group them intro two categories, first cpp files (.h extension) and second C# files (.cs extension). C# files are now compiled with other project files into final settings registry assembly.

Cpp files are compiled with the client application.

<img src="CodeGenBuild.svg"/>

## Classes

CodeGen consist multiple _CodeWriter_, each _CodeWriter_ is responsible for providing a small subset of functionality.
_CodeWriters_ results are combined into single or multiple file; each _CodeWriter_ specifies the output file.

## Hierarchy of CodeWriters:

### Namespaces

- `Mlos.SettingsSystem.CodeGen.CodeWriters.CppTypesCodeWriters`

    - CodeGens in this namespace write Cpp struct and proxy view defintions.

- `Mlos.SettingsSystem.CodeGen.CodeWriters.PythonCodeWriters`

    - Creates python bindings.

- `Mlos.SettingsSystem.CodeGen.CodeWriters.CppObjectExchangeCodeWriters`

    - Creates set of classes and functions that enables exchange generated objects.
    This includes helper classes returning type index, serialization and deserialization handlers.

## Basic structure generation

### CppObjectCodeWriter

Creates a regular Cpp structure based on CSharp type.

From the following CSharp code:

```CSharp
namespace Mlos.Core.Channel
{
    /// <summary>
    /// Shared circular buffer channel settings.
    /// </summary>
    struct ChannelSettings
    {
        /// <summary>
        /// Size of the buffer. To avoid arithmetic overflow, buffer size must be power of two
        /// </summary>
        int BufferSize;

        /// <summary>
        /// Number of reader using this channel.
        /// </summary>
        int ReaderCount;
    }
}
```

From this definition _CppObjectCodeWriter_ generates code:

```C++
namespace MLOS
{
namespace Core
{
namespace Channel
{
    // Shared circular buffer channel settings.
    //
    struct ChannelSettings
    {

        // Size of the buffer. To avoid arithmetic overflow, buffer size must be power of two
        //
        int32_t BufferSize;

        // Number of reader using this channel.
        //
        int32_t ReaderCount;
    };
}
}
}
```

Codegen is using CSharp namespaces.


### CppProxyCodeWriter

Creates a view to a Cpp structure. To be more precise, creates a view to serialized form of the structure.
Allows to read structure fields after they are serialized in the exchange buffer.

```C++
namespace Proxy
{

namespace MLOS
{
namespace Core
{
namespace Channel
{

struct ChannelReaderStats : public PropertyProxy<ChannelReaderStats>
{
    typedef ::MLOS::Core::Channel::ChannelReaderStats RealObjectType;

    ChannelReaderStats(FlatBuffer& flatBuffer, uint32_t offset = 0)
     :  PropertyProxy<ChannelReaderStats>(flatBuffer, offset)
    {}
    PropertyProxy<uint64_t> MessagesRead = PropertyProxy<uint64_t>(flatBuffer, offset + 0);
    PropertyProxy<uint64_t> SpinCount = PropertyProxy<uint64_t>(flatBuffer, offset + 8);
};

}
}
}

}
```

CppProxyCodeWriter creates objects in **Proxy** namespace, so we can easily distinguish between structure and structure proxy.

```C++
MLOS::Core::Channel::ChannelReaderStats object;
Proxy::MLOS::Core::Channel::ChannelReaderStats proxyView;
```


### CppEnumCodeWriter
Creates a Cpp enums. As enum is a primitive type, there is no proxy class for the enum types.

```CSharp
enum Colors : ulong
{
    Red = 2,
    Green = 5,
    Blue = 9
};
```

```C++
enum Colors : uint64_t
{
    Red = 2,
    Green = 5,
    Blue = 9,
};
```

## Serialization

### Basics

Serialization requires type identifier.
The identifier must be the same for the sender and for the receiver.
The sender needs to know the type id during the compilation, so function returning type identifier must use constexpr modifier.
The receiver is using type id to find and call proper handler. The receiver does not need to know type identifier during the compilations and dispatch invocation is always dynamic.

### Current implementation
For each type, CodeGen creates a specialized method TypeMetadataInfo::Index&lt;T&gt; which returns a unique id.
To simplify dispatcher code, ids are simply type indexes.

```Cpp
namespace TypeMetadataInfo
{
    template<typename T>
    static constexpr uint32_t Index();

    template <>
    constexpr uint32_t Index<Point>() { return DispatchTableBaseIndex() + 1; }

    template <>
    constexpr uint32_t Index<Point3D>() { return DispatchTableBaseIndex() + 2; }

    template <>
    constexpr uint32_t Index<Line>() { return DispatchTableBaseIndex() + 3; }
    ...
}
```

The CodeGen is creating a dispatcher table:

```Cpp

__declspec(selectany) ::MLOS::Core::DispatchEntry DispatchTable[] =
   {
       ::MLOS::Core::DispatchEntry
       {
           TypeMetadataInfo::Index<::SqlServer::Spatial::Point>(),
           [](FlatBuffer&& buffer)
           {
               Proxy::SqlServer::Spatial::Point recvObjectProxy(buffer);
               ObjectDeserializationCallback::Deserialize(std::move(recvObjectProxy));
           }
       }
       ...
   }
```
Because we are using type indexes, finding a dispatcher routine is a matter of simple table lookup.
To verify if sender and receiver processes are using the same table, sender will  include the hash created from the type definition. That allows receiver to reject invalid/type mismatched frames.

Special steps are table to enable usage of multiple dispatch tables. Each dispatch table must have a unique base index. All type indexes included in this dispatch table will be incremented by the base table index. Base index of next dispatch table is equal to base index of the previous table plus number of types of previous table.


```Cpp
// Base indexes for all included dispatcher tables.
//
constexpr uint32_t MLOS::Core::Channel::ObjectDeserializationHandler::DispatchTableBaseIndex() { return 0; }
constexpr uint32_t SqlServer::Spatial::ObjectDeserializationHandler::DispatchTableBaseIndex() { return MLOS::Core::Channel::ObjectDeserializationHandlerHandler::DispatTableElementCount(); }
```

Global dispatch table (concatenation of all included dispatch tables) is created during the compilation.

```Cpp
constexpr auto GlobalDispatchTable()
{
    auto globalDispatchTable = MLOS::Core::DispatchTable<0>()
        .concatenate(MLOS::Core::Channel::ObjectDeserializationHandler::DispatchTable)
        .concatenate(SqlServer::Spatial::ObjectDeserializationHandler::DispatchTable);

    return globalDispatchTable;
}
```

### Alternative
Use type hash as identifier. Receiver would need to perform a lookup (hashmap, if/else sequence, binary search, binary search with if/else sequence) to find the correct dispatch function.

_#TODO revisit after implementing C# dispatch handlers_

### CppObjectSerializeCodeWriter

### CppObjectSerializedLengthCodeWriter

...
... #TODO
... more stuff needs to go here
...

## Runtime callback handlers

Runtime callback handlers allow the developer to dynamically change the callback code.


### CppObjectDeserializeRuntimeCallbackCodeWriter

For each type, codegen will generate a callback that can be set in runtime.
Root callback namespace is _ObjectDeserializationCallback_, callbacks for types are created in type namespace.


```Cpp
namespace ObjectDeserializationCallback
{
    namespace _Type_Namespace_
    {
    __declspec(selectany) std::function<void (::Proxy::SqlServer::Spatial::Point&&)> Point_Callback = nullptr;
    __declspec(selectany) std::function<void (::Proxy::SqlServer::Spatial::Point3D&&)> Point3D_Callback = nullptr;
    ...
    }
}
```

Example of setting runtime callback, test code is verifying the received object.

```Cpp
ObjectDeserializationCallback::SqlServer::Spatial::Point_Callback = [point](Proxy::SqlServer::Spatial::Point&& recvPoint)
{
    float x = recvPoint.x;
    float y = recvPoint.y;

    EXPECT_EQ(point.x, x);
    EXPECT_EQ(point.y, y);
};
```


### CppObjectDeserializeFunctionCallbackCodeWriter

CodeGen will generate a set of handlers with default action to call proper callback.

```Cpp
namespace ObjectDeserializationCallback
{
    template <>
    inline void Deserialize<::Proxy::SqlServer::Spatial::Point>(::Proxy::SqlServer::Spatial::Point&& obj)
    {
        ::ObjectDeserializationCallback::SqlServer::Spatial::Point_Callback(std::move(obj));
    }

    template <>
    inline void Deserialize<::Proxy::SqlServer::Spatial::Point3D>(::Proxy::SqlServer::Spatial::Point3D&& obj)
    {
        ::ObjectDeserializationCallback::SqlServer::Spatial::Point3D_Callback(std::move(obj));
    }
```

There is performance overhead related to std::function call. However runtime callbacks provide a great
flexibility and allow runtime changing the callback handlers. Therefore primary usage for runtime handler is test.
