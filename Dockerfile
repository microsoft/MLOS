# A Dockerfile for creating a suitable build environment for MLOS for testing
# the various versions of Ubuntu we need to support.

# Supported UbuntuVersions: 16.04, 18.04, 20.04
#
# Build with:
#   UbuntuVersion=20.04; docker build --build-arg=UbuntuVersion=$UbuntuVersion -t mlos/build:ubuntu-$UbuntuVersion .
#
# Optionally, build with a proxy server:
#   UbuntuVersion=20.04; docker build --build-arg=http_proxy=http://some-proxy-caching-host:3128 --build-arg=UbuntuVersion=$UbuntuVersion -t mlos/build:ubuntu-$UbuntuVersion .
#
# Run with:
#   docker run -it --name mlos-build-$UbuntuVersion mlos/build:ubuntu-$UbuntuVersion
#
# Alternatively, if you want to map the current source tree into the container
# instead of using a separate copy from the build step:
#   docker run -v `pwd`:/src/MLOS -it --name mlos-build-$UbuntuVersion mlos/build:ubuntu-$UbuntuVersion
#
# The latter allows live editing in a native editor (e.g. VSCode or
# VisualStudio) and building using the container's environment.
#
# Once inside the container the `make` command will handle typical build needs.
#
# To restart an existing container:
#   docker start -i mlos-build-$UbuntuVersion

# The default version of Ubuntu to use.
# This is currently set to 16.04 since that is the version that SqlServer
# supports.  See above for ways to override this.
ARG UbuntuVersion=16.04

FROM --platform=linux/amd64 ubuntu:${UbuntuVersion}

ARG DEBIAN_FRONTEND=noninteractive
ARG TZ=UTC
ARG LANG=en_US.UTF-8

# Setup the tzdata and locale early on so it doesn't prompt or spit warnings at us.
RUN apt-get update && \
    LANG=C apt-get --no-install-recommends -y install apt-utils && \
    LANG=C apt-get --no-install-recommends -y install locales && \
    locale-gen ${LANG} && update-locale LANG=${LANG} && \
    DEBIAN_FRONTEND=${DEBIAN_FRONTEND} TZ=${TZ} \
        apt-get --no-install-recommends -y install tzdata && \
    DEBIAN_FRONTEND=${DEBIAN_FRONTEND} TZ=${TZ} \
        dpkg-reconfigure tzdata

# Start setting up the container image to include the necessary build tools.
RUN apt-get update && \
    apt-get --no-install-recommends -y install \
        git make build-essential sudo curl wget lsb-release \
        software-properties-common apt-transport-https apt-utils \
        exuberant-ctags vim-nox bash-completion less

# A few quality of life improvements:
# Don't beep/bell on tab completion failure.
RUN echo "set bell-style none" >> /etc/inputrc

# Install python3.7 and its pip dependencies
RUN mkdir -p /tmp/MLOS/scripts
COPY ./scripts/install.python.sh /tmp/MLOS/scripts/
RUN /bin/bash /tmp/MLOS/scripts/install.python.sh

RUN apt-get update && \
    apt-get --no-install-recommends -y install \
        libfreetype6-dev unixodbc-dev

RUN python3.7 -m pip install pip && \
    python3.7 -m pip install --upgrade pip && \
    python3.7 -m pip install setuptools

COPY ./source/Mlos.Python/requirements.txt /tmp/
RUN python3.7 -m pip install -r /tmp/requirements.txt

# Install LLVM using our script.
RUN mkdir -p /tmp/MLOS/scripts
COPY ./scripts/install.llvm-clang.sh /tmp/MLOS/scripts/
RUN apt-get update && \
    apt-get --no-install-recommends -y install \
        gnupg-agent && \
    /bin/bash /tmp/MLOS/scripts/install.llvm-clang.sh

# Install some dependencies necessary for dotnet.
# Older versions of Ubuntu need additional libcurl libraries not already pulled
# in by the curl binary.
RUN if [ v`lsb_release -s -r` = 'v16.04' ]; then \
        apt-get --no-install-recommends -y install libcurl3; \
    fi
# Note: libxml2 automatically pulls in an appropriate version of the ^libicu[0-9]+$ package.
RUN apt-get --no-install-recommends -y install liblttng-ctl0 liblttng-ust0 libxml2 zlib1g

# Cleanup the apt caches from the image.
RUN apt-get -y clean && rm -rf /var/lib/apt/lists/*

# Prefetch the necessary local build tools/dependencies.
COPY ./scripts/fetch-cmake.sh \
    ./scripts/fetch-dotnet.sh ./scripts/dotnet.env ./scripts/util.sh ./scripts/dotnet \
    /src/MLOS/scripts/
RUN cd /src/MLOS && \
    ./scripts/fetch-cmake.sh && \
    ./tools/bin/cmake --help >/dev/null && \
    ./scripts/fetch-dotnet.sh && \
    ./tools/bin/dotnet help >/dev/null

# Whether or not to include extras to make interactive editing inside the
# container using "docker exec" somewhat more reasonable.
# Run the docker build command with an additional "--build-arg=WithExtras=true"
# to install them as well.
ARG WithExtras=false
RUN if [ "x$WithExtras" = "xtrue" ]; then \
        apt-get update && \
        apt-get -y install \
            man man-db manpages manpages-dev && \
        /etc/cron.weekly/man-db; \
    fi

# Copy the current MLOS source tree into /src/MLOS so that it can also be
# executed standalone without a bind mount.
# Note: due to the recursive copy, this step is not very cacheable.
COPY ./ /src/MLOS/

# Declare a volume that we can bind mount the current MLOS repo into in-place
# instead of the default copy.
VOLUME /src/MLOS

# Mark the output directories as separate volumes so that we can reuse the live
# source tree across different container build targets without conflicting
# cmake or build outputs.
VOLUME /src/MLOS/out
VOLUME /src/MLOS/target

WORKDIR /src/MLOS

# By default execute a bash shell for interactive usage.
# This can also be overridden on the "docker run" command line with
# "make" to execute a build and exit for pipeline usage instead.
CMD ["/bin/bash", "-l"]
