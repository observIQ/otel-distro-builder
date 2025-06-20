# Start with an official Python 3 image as the base
FROM python:3.13.5-slim-bookworm

# Version definitions for easy updates
ENV GORELEASER_VERSION=2.8.1
ENV SYFT_VERSION=1.21.0
ENV OCB_VERSIONS="0.120.0 0.121.0 0.122.0"
ENV GO_VERSIONS="1.24.1"
ENV DEFAULT_GO_VERSION="1.24.1"

# Install essential libraries for Go, glibc compatibility, and ARM support
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    libc6 \
    git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Set architecture variable
ARG TARGETARCH
ENV TARGETARCH=${TARGETARCH:-amd64}

# Install multiple Go versions
RUN mkdir -p /usr/local/go-versions && \
    for version in $GO_VERSIONS; do \
    wget -q -O- https://dl.google.com/go/go${version}.linux-${TARGETARCH}.tar.gz | tar -C /usr/local/go-versions -xzf - && \
    mv /usr/local/go-versions/go /usr/local/go-versions/go${version}; \
    done && \
    ln -s /usr/local/go-versions/go${DEFAULT_GO_VERSION}/bin/go /usr/bin/go

# Add script to switch Go versions
RUN echo '#!/bin/bash\n\
    if [ -z "$1" ]; then\n\
    echo "Usage: switch-go <version>"\n\
    echo "Available versions: ${GO_VERSIONS}"\n\
    exit 1\n\
    fi\n\
    if [ -d "/usr/local/go-versions/go$1" ]; then\n\
    rm -f /usr/bin/go\n\
    ln -s /usr/local/go-versions/go$1/bin/go /usr/bin/go\n\
    echo "Switched to Go $1"\n\
    else\n\
    echo "Go version $1 not found"\n\
    exit 1\n\
    fi' > /usr/local/bin/switch-go && \
    chmod +x /usr/local/bin/switch-go

# Install goreleaser based on architecture
RUN if [ "$TARGETARCH" = "arm64" ]; then \
    wget -q -O- https://github.com/goreleaser/goreleaser-pro/releases/download/v${GORELEASER_VERSION}/goreleaser-pro_Linux_arm64.tar.gz | tar -C /usr/local/bin -xzf - goreleaser; \
    else \
    wget -q -O- https://github.com/goreleaser/goreleaser-pro/releases/download/v${GORELEASER_VERSION}/goreleaser-pro_Linux_x86_64.tar.gz | tar -C /usr/local/bin -xzf - goreleaser; \
    fi && \
    chmod +x /usr/local/bin/goreleaser

# Install syft for SBOM generation
RUN wget -q -O- https://github.com/anchore/syft/releases/download/v${SYFT_VERSION}/syft_${SYFT_VERSION}_linux_${TARGETARCH}.tar.gz | \
    tar -C /usr/local/bin -xzf - syft && \
    chmod +x /usr/local/bin/syft

# Set environment variables for Go and Python paths
ENV GOPATH=/go
ENV PATH=$PATH:/usr/local/go/bin:$GOPATH/bin

# Set up directories for application code
WORKDIR /app

# Pre-install OpenTelemetry Collector Builder versions
RUN mkdir -p /app/ocb
RUN for OCB_VERSION in $OCB_VERSIONS; do \
    wget -O ocb/ocb_${OCB_VERSION}_linux_${TARGETARCH} \
    "https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/cmd%2Fbuilder%2Fv${OCB_VERSION}/ocb_${OCB_VERSION}_linux_${TARGETARCH}" && \
    chmod 755 ocb/ocb_${OCB_VERSION}_linux_${TARGETARCH}; \
    done

# Create standard directories for input/output
RUN mkdir -p /build && \
    mkdir -p /artifacts

# Copy only the required files
COPY . /app/builder/

# Make entrypoint script executable
RUN chmod +x /app/builder/entrypoint.sh

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/builder/requirements.txt

# Set the entrypoint to our script
ENTRYPOINT ["/app/builder/entrypoint.sh"]

# Default to showing help
CMD ["--help"]
