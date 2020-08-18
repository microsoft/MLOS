#pragma once

namespace Mlos
{
namespace Core
{

class NamedEvent
{
public:
    NamedEvent() noexcept;

    NamedEvent(NamedEvent&& namedEvent) noexcept;

    ~NamedEvent();

    _Check_return_
    HRESULT CreateOrOpen(const char* const namedEventName) noexcept;

    _Check_return_
    HRESULT Open(const char* const namedEventName) noexcept;

    void Signal();

    void Wait();

private:
};

}
}