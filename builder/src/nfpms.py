nfpms_config = """
nfpms:
  - package_name: __DISTRIBUTION__
    file_name_template: '{{ .PackageName }}_v{{ .Version }}_{{ .Os }}_{{ .Arch }}{{ with .Arm }}v{{ . }}{{ end }}{{ with .Mips }}_{{ . }}{{ end }}{{ if not (eq .Amd64 "v1") }}{{ .Amd64 }}{{ end }}'
    bindir: /opt/__DISTRIBUTION__
    scripts:
      preinstall: preinstall.sh
      postinstall: postinstall.sh
      preremove: preremove.sh
    id: __DISTRIBUTION__
    ids:
      - __DISTRIBUTION__
    formats:
      - apk
      - deb
      - rpm
    description: OpenTelemetry Collector with OpAMP Supervisor - __DISTRIBUTION__
    license: Apache 2.0
    contents:
      # systemd service files
      - src: __DISTRIBUTION__.service
        dst: /lib/systemd/system/__DISTRIBUTION__.service
        file_info:
          mode: 0644
          owner: root
          group: root
      - src: __DISTRIBUTION__.conf
        dst: /etc/__DISTRIBUTION__/__DISTRIBUTION__.conf
        type: config|noreplace
        file_info:
          mode: 0644
          owner: root
          group: root

      # directory and files for the OpenTelemetry Collector distribution
      - dst: /opt/__DISTRIBUTION__
        type: dir
        file_info:
          mode: 0755
          owner: __DISTRIBUTION__
          group: __DISTRIBUTION__
      - src: _contrib/supervisor_{{.Os}}_{{.Arch}}{{ .ArtifactExt }}
        dst: /opt/__DISTRIBUTION__/supervisor{{ .ArtifactExt }}
        file_info:
          mode: 0755
          owner: __DISTRIBUTION__
          group: __DISTRIBUTION__
      - src: supervisor_config.yaml
        dst: /opt/__DISTRIBUTION__/supervisor_config.yaml
        file_info:
          mode: 0644
          owner: __DISTRIBUTION__
          group: __DISTRIBUTION__
      - dst: /opt/__DISTRIBUTION__/supervisor_storage
        type: dir
        file_info:
          mode: 0750
          owner: __DISTRIBUTION__
          group: __DISTRIBUTION__

  - package_name: __DISTRIBUTION___otelcol
    file_name_template: '{{ .PackageName }}_v{{ .Version }}_{{ .Os }}_{{ .Arch }}{{ with .Arm }}v{{ . }}{{ end }}{{ with .Mips }}_{{ . }}{{ end }}{{ if not (eq .Amd64 "v1") }}{{ .Amd64 }}{{ end }}'
    bindir: /opt/__DISTRIBUTION__
    scripts:
      preinstall: preinstall.sh
      postinstall: postinstall.sh
      preremove: preremove.sh
    id: __DISTRIBUTION___otelcol
    ids:
      - __DISTRIBUTION__
    formats:
      - apk
      - deb
      - rpm
    description: OpenTelemetry Collector - __DISTRIBUTION__
    license: Apache 2.0
    contents:
      # systemd service files
      - src: __DISTRIBUTION___otelcol.service
        dst: /lib/systemd/system/__DISTRIBUTION__.service
        file_info:
          mode: 0644
          owner: root
          group: root
      - src: __DISTRIBUTION___otelcol.conf
        dst: /etc/__DISTRIBUTION__/__DISTRIBUTION__.conf
        type: config|noreplace
        file_info:
          mode: 0644
          owner: root
          group: root

      # directory and files for the OpenTelemetry Collector distribution
      - dst: /opt/__DISTRIBUTION__
        type: dir
        file_info:
          mode: 0755
          owner: __DISTRIBUTION__
          group: __DISTRIBUTION__
      - src: collector_config.yaml
        dst: /opt/__DISTRIBUTION__/collector_config.yaml
        file_info:
          mode: 0644
          owner: __DISTRIBUTION__
          group: __DISTRIBUTION__

"""