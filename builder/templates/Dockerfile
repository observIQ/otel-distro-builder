FROM alpine:3.19 as certs
RUN apk --update add ca-certificates

FROM scratch

ARG USER_UID=10001
USER ${USER_UID}

COPY --from=certs /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt

# Copy the OpenTelemetry Collector binary
COPY --chmod=755 __DISTRIBUTION__ /__DISTRIBUTION__

# Copy the supervisor binary
COPY --chmod=755 _contrib/supervisor_linux_amd64 /__DISTRIBUTION__/supervisor

# Copy the supervisor config
COPY supervisor_config.yaml /etc/__DISTRIBUTION__/supervisor_config.yaml

ENTRYPOINT ["/__DISTRIBUTION__/supervisor"]
CMD ["--config", "/etc/__DISTRIBUTION__/supervisor_config.yaml"]
EXPOSE 4317 55678 55679
