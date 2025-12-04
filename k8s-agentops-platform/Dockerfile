# Multi-stage build for Agent Controller

# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /workspace

# Copy go mod files
COPY controller/go.mod controller/go.sum ./
RUN go mod download

# Copy source code
COPY controller/ ./

# Build
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -a -installsuffix cgo \
    -ldflags='-w -s -extldflags "-static"' \
    -o controller cmd/main.go

# Runtime stage
FROM gcr.io/distroless/static:nonroot

WORKDIR /

COPY --from=builder /workspace/controller /controller

USER 65532:65532

ENTRYPOINT ["/controller"]
