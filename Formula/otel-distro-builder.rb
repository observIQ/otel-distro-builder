# Homebrew formula for otel-distro-builder.
# Install from this repo: brew install --formula Formula/otel-distro-builder.rb
# Or from a tap (when available): brew tap observiq/tap && brew install otel-distro-builder
#
# On each release, update version and the sha256 for each platform (run:
# curl -sL <url> | shasum -a 256).

class OtelDistroBuilder < Formula
  desc "Build and package custom OpenTelemetry Collector distributions"
  homepage "https://github.com/observiq/otel-distro-builder"
  version "1.0.0"

  on_macos do
    on_arm do
      url "https://github.com/observiq/otel-distro-builder/releases/download/v1.0.0/otel-distro-builder-1.0.0-darwin-arm64.tar.gz"
      sha256 "0000000000000000000000000000000000000000000000000000000000000000"
    end
    on_intel do
      url "https://github.com/observiq/otel-distro-builder/releases/download/v1.0.0/otel-distro-builder-1.0.0-darwin-amd64.tar.gz"
      sha256 "0000000000000000000000000000000000000000000000000000000000000000"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/observiq/otel-distro-builder/releases/download/v1.0.0/otel-distro-builder-1.0.0-linux-arm64.tar.gz"
      sha256 "0000000000000000000000000000000000000000000000000000000000000000"
    end
    on_intel do
      url "https://github.com/observiq/otel-distro-builder/releases/download/v1.0.0/otel-distro-builder-1.0.0-linux-amd64.tar.gz"
      sha256 "0000000000000000000000000000000000000000000000000000000000000000"
    end
  end

  def install
    # Tarball contains a single file: otel-distro-builder-<os>-<arch>
    bin.install Dir["otel-distro-builder-*"].first => "otel-distro-builder"
  end

  test do
    assert_match "usage:", shell_output("#{bin}/otel-distro-builder --help")
  end
end
