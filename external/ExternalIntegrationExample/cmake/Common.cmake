# This file would contain whatever common build definitions the external project needed.

set(CMAKE_CXX_STANDARD 14)

# In our example, we want to enforce very strict compiler warnings to make sure
# the MLOS code we include will work easily in most places.
add_compile_options(-Wall -Wextra -Wpedantic -Werror)
add_link_options(-Wall -Wextra -Wpedantic -Werror)

# Include debug symbols.
add_compile_options(-g)
add_link_options(-g)
