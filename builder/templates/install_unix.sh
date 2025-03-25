#!/bin/sh
set -e

# Constants
REPOSITORY_URL="__REPO__"
INSTALL_DIR="/opt/__DISTRIBUTION__"
SUPERVISOR_YML_PATH="$INSTALL_DIR/supervisor-config.yaml"
PREREQS="curl printf"

usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Optional arguments:"
    echo "  -v, --version VERSION    Specify version to install (default: latest)"
    echo "  -b, --base-url URL      GitHub repository URL (e.g., 'https://github.com/org/repo')"
    echo "  -e, --endpoint URL      OpAMP endpoint (default: ws://localhost:3001/v1/opamp)"
    echo "  -s, --secret-key KEY    OpAMP secret key"
    echo "  -l, --labels LABELS     Comma-separated list of labels (e.g., 'env=prod,region=us-west')"
    echo "  -u, --uninstall         Uninstall the package"
    echo "  -h, --help              Show this help message"
    exit 1
}

manage_service() {
    echo "Managing service state..."
    if ! command -v systemctl >/dev/null; then
        echo "Warning: systemd not found, service not enabled"
        echo "You will need to manually start the service"
        return
    fi

    # Reload systemd to pick up any changes
    systemctl daemon-reload

    # Check if service is already enabled
    if ! systemctl is-enabled __DISTRIBUTION__ >/dev/null 2>&1; then
        echo "Enabling __DISTRIBUTION__ service..."
        systemctl enable __DISTRIBUTION__
    fi

    # Check if service is already running
    if systemctl is-active __DISTRIBUTION__ >/dev/null 2>&1; then
        echo "Restarting __DISTRIBUTION__ service..."
        systemctl restart __DISTRIBUTION__
    else
        echo "Starting __DISTRIBUTION__ service..."
        systemctl start __DISTRIBUTION__
    fi

    # Verify service status
    if systemctl is-active __DISTRIBUTION__ >/dev/null 2>&1; then
        echo "Service is running"
    else
        echo "Warning: Service failed to start. Check status with: systemctl status __DISTRIBUTION__"
        exit 1
    fi
}

set_permissions() {
    echo "Setting permissions..."
    chown -R __DISTRIBUTION__:__DISTRIBUTION__ "$INSTALL_DIR"
}

create_supervisor_config() {
    echo "Creating supervisor config..."
    if [ -z "$OPAMP_ENDPOINT" ]; then
        OPAMP_ENDPOINT="ws://localhost:3001/v1/opamp"
        echo "No OpAMP endpoint specified, using default: $OPAMP_ENDPOINT"
    fi

    # Create empty file and set permissions before writing sensitive data
    command printf '' >"$SUPERVISOR_YML_PATH"
    chown __DISTRIBUTION__:__DISTRIBUTION__ "$SUPERVISOR_YML_PATH"
    chmod 0600 "$SUPERVISOR_YML_PATH"

    # Write configuration line by line
    command printf 'server:\n' >"$SUPERVISOR_YML_PATH"
    command printf '  endpoint: "%s"\n' "$OPAMP_ENDPOINT" >>"$SUPERVISOR_YML_PATH"

    if [ -n "$OPAMP_SECRET_KEY" ]; then
        command printf '  headers:\n' >>"$SUPERVISOR_YML_PATH"
        command printf '    Authorization: "Secret-Key %s"\n' "$OPAMP_SECRET_KEY" >>"$SUPERVISOR_YML_PATH"
    fi

    command printf '  tls:\n' >>"$SUPERVISOR_YML_PATH"
    command printf '    insecure: true\n' >>"$SUPERVISOR_YML_PATH"
    command printf '    insecure_skip_verify: true\n' >>"$SUPERVISOR_YML_PATH"
    command printf 'capabilities:\n' >>"$SUPERVISOR_YML_PATH"
    command printf '  accepts_remote_config: true\n' >>"$SUPERVISOR_YML_PATH"
    command printf '  reports_remote_config: true\n' >>"$SUPERVISOR_YML_PATH"
    command printf 'agent:\n' >>"$SUPERVISOR_YML_PATH"
    command printf '  executable: "%s"\n' "$INSTALL_DIR/__DISTRIBUTION__" >>"$SUPERVISOR_YML_PATH"
    command printf '  config_apply_timeout: 30s\n' >>"$SUPERVISOR_YML_PATH"
    command printf '  bootstrap_timeout: 5s\n' >>"$SUPERVISOR_YML_PATH"

    if [ -n "$OPAMP_LABELS" ]; then
        command printf '  description:\n' >>"$SUPERVISOR_YML_PATH"
        command printf '    non_identifying_attributes:\n' >>"$SUPERVISOR_YML_PATH"
        command printf '      service.labels: "%s"\n' "$OPAMP_LABELS" >>"$SUPERVISOR_YML_PATH"
    fi

    command printf 'storage:\n' >>"$SUPERVISOR_YML_PATH"
    command printf '  directory: "%s"\n' "$INSTALL_DIR/supervisor_storage" >>"$SUPERVISOR_YML_PATH"
    command printf 'telemetry:\n' >>"$SUPERVISOR_YML_PATH"
    command printf '  logs:\n' >>"$SUPERVISOR_YML_PATH"
    command printf '    level: 0\n' >>"$SUPERVISOR_YML_PATH"
    command printf '    output_paths: ["%s"]\n' "$INSTALL_DIR/supervisor.log" >>"$SUPERVISOR_YML_PATH"
}

set_os_arch() {
    os_arch=$(uname -m)
    case "$os_arch" in
    # arm64 strings. These are from https://stackoverflow.com/questions/45125516/possible-values-for-uname-m
    aarch64 | arm64 | aarch64_be | armv8b | armv8l)
        os_arch="arm64"
        ;;
    x86_64)
        os_arch="amd64"
        ;;
    # experimental PowerPC arch support for collector
    ppc64)
        os_arch="ppc64"
        ;;
    ppc64le)
        os_arch="ppc64le"
        ;;
    # armv6/32bit. These are what raspberry pi can return, which is the main reason we support 32-bit arm
    arm | armv6l | armv7l)
        os_arch="arm"
        ;;
    *)
        echo "Unsupported os arch: $os_arch"
        exit 1
        ;;
    esac
}

download_and_install() {
    set_os_arch
    local download_url="${repository_url}/releases/download/v${version}/__DISTRIBUTION___v${version}_linux_${os_arch}.${pkg_type}"
    echo "Downloading: $download_url"

    case "$pkg_type" in
    tar.gz)
        mkdir -p "$INSTALL_DIR"
        curl -L "$download_url" | tar xz -C "$INSTALL_DIR"
        ;;
    deb)
        local tmp_file="/tmp/__DISTRIBUTION___${version}.deb"
        curl -L "$download_url" -o "$tmp_file"
        dpkg -i "$tmp_file"
        rm -f "$tmp_file"
        ;;
    rpm)
        local tmp_file="/tmp/__DISTRIBUTION___${version}.rpm"
        curl -L "$download_url" -o "$tmp_file"
        rpm -U "$tmp_file"
        rm -f "$tmp_file"
        ;;
    esac
}

detect_package_type() {
    if command -v dpkg >/dev/null 2>&1; then
        pkg_type="deb"
    elif command -v rpm >/dev/null 2>&1; then
        pkg_type="rpm"
    else
        pkg_type="tar.gz"
    fi
    echo "Auto-detected package type: $pkg_type"
}

dependencies_check() {
    FAILED_PREREQS=''
    for prerequisite in $PREREQS; do
        if command -v "$prerequisite" >/dev/null; then
            continue
        else
            if [ -z "$FAILED_PREREQS" ]; then
                FAILED_PREREQS="$prerequisite"
            else
                FAILED_PREREQS="$FAILED_PREREQS, $prerequisite"
            fi
        fi
    done

    if [ -n "$FAILED_PREREQS" ]; then
        echo "The following dependencies are required by this script: [$FAILED_PREREQS]"
        exit 1
    fi
}

install() {
    dependencies_check
    detect_package_type
    download_and_install
    create_supervisor_config
    set_permissions
    manage_service

    echo "Installation complete!"
    echo "Installation directory: $INSTALL_DIR"
    echo "Supervisor config: $SUPERVISOR_YML_PATH"
}

uninstall() {
    echo "Uninstalling __DISTRIBUTION__..."
    if command -v systemctl >/dev/null; then
        systemctl stop __DISTRIBUTION__ >/dev/null 2>&1 || true
        systemctl disable __DISTRIBUTION__ >/dev/null 2>&1 || true
    fi

    # Remove package if it was installed via package manager
    if command -v dpkg >/dev/null 2>&1; then
        dpkg -r __DISTRIBUTION__ >/dev/null 2>&1 || true
    elif command -v rpm >/dev/null 2>&1; then
        rpm -e __DISTRIBUTION__ >/dev/null 2>&1 || true
    fi

    rm -rf "$INSTALL_DIR"
    echo "Uninstallation complete"
}

get_repository_url() {
    if [ -n "$base_url" ]; then
        repository_url="$base_url"
    elif [ -n "$REPOSITORY_URL" ]; then
        repository_url="$REPOSITORY_URL"
    else
        echo "Error: No repository URL specified. Please either:"
        echo "  1. Use the -b/--base-url option"
        echo "  2. Set the REPOSITORY_URL constant in the script"
        exit 1
    fi
    echo "Using repository URL: $repository_url"
}

parse_args() {
    # Set default version
    version="latest"

    while [ -n "$1" ]; do
        case "$1" in
        -v | --version)
            version=$2
            shift 2
            ;;
        -b | --base-url)
            base_url=$2
            shift 2
            ;;
        -e | --endpoint)
            OPAMP_ENDPOINT=$2
            shift 2
            ;;
        -s | --secret-key)
            OPAMP_SECRET_KEY=$2
            shift 2
            ;;
        -l | --labels)
            OPAMP_LABELS=$2
            shift 2
            ;;
        -u | --uninstall)
            uninstall
            exit 0
            ;;
        -h | --help)
            usage
            ;;
        *)
            echo "Invalid argument: $1"
            usage
            ;;
        esac
    done

    # Determine repository URL to use
    get_repository_url
}

check_root() {
    if [ "$(id -u)" != "0" ]; then
        echo "This script must be run as root"
        exit 1
    fi
}

main() {
    check_root
    parse_args "$@"
    install
}

main "$@"
