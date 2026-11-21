FROM golang:1.24-alpine AS build

RUN CGO_ENABLED=0 GOBIN=/out go install github.com/minio/minio@RELEASE.2025-09-06T17-38-46Z

FROM alpine:3.22

RUN apk add --no-cache ca-certificates
COPY --from=build /out/minio /usr/local/bin/minio

ENTRYPOINT ["/usr/local/bin/minio"]
CMD ["server", "/data"]
