#!/bin/bash
# Shared helpers for local build scripts.
# Source this file; do not execute directly.

# Echo the Docker platform (linux/amd64 or linux/arm64) for the current host.
# Used so the builder image runs natively and avoids QEMU emulation (which can
# cause OCB to crash on arm64).
get_docker_platform() {
    local arch
    arch=$(uname -m)
    case "$arch" in
        x86_64) echo "linux/amd64" ;;
        arm64|aarch64) echo "linux/arm64" ;;
        *) echo "linux/amd64" ;;
    esac
}
