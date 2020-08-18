#pragma once

#include <thread>         // std::this_thread::sleep_for
#include <chrono>         // std::chrono::seconds

namespace Mlos
{
namespace Core
{
namespace Internal
{

inline void Platform::Terminate()
{
    std::terminate();
}

inline void Platform::Wait()
{
    std::this_thread::sleep_for(std::chrono::seconds(1));
}

}
}
}
