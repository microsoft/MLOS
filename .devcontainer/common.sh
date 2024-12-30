##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##
case $OSTYPE in
    linux*)
        STAT_FORMAT_GID_ARGS="-c%g"
        STAT_FORMAT_INODE_ARGS="-c%i"
        ;;
    darwin*)
        STAT_FORMAT_GID_ARGS="-f%g"
        STAT_FORMAT_INODE_ARGS="-f%i"
        ;;
    *)
        echo "ERROR: Unhandled OSTYPE: $OSTYPE"
        exit 1
        ;;
esac
