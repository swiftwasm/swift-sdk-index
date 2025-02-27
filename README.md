# Swift SDK index

This repository hosts static information needed for selecting appropriate Swift SDK versions during installation.

## Repository Structure

```
/
└── v1/
    ├── tag-by-version.json       # Maps `swiftc --version | head -n1` output to swift.org release tags
    └── builds/                   # Build information directory
        ├── swift-6.0.3-RELEASE.json
        ├── swift-DEVELOPMENT-SNAPSHOT-2024-10-31-a.json
        └── ... (other version files)
```

## Key Files

### `v1/tag-by-version.json`

This file maps `swiftc --version | head -n1` output to swift.org release tags:

```json
{
  "Swift version 6.0.3 (swift-6.0.3-RELEASE)": [
    "swift-6.0.3-RELEASE"
  ],
  "Swift version 6.1-dev (LLVM 42f3e8ef873e24d, Swift c690fefef71c26a)": [
    "swift-DEVELOPMENT-SNAPSHOT-2024-11-28-a",
    "swift-DEVELOPMENT-SNAPSHOT-2024-11-29-a"
  ],
  "Swift version 6.2-dev (LLVM 23dd6ab259a178a, Swift a4a3a41b50e111e)": [
    "swift-DEVELOPMENT-SNAPSHOT-2025-02-18-a"
  ]
}
```

### `v1/builds/{TAG}.json`

Contains build information for each tag:

```json
{
  "metadata": {
    "versions": {
      "swift": "swift-6.0.3-RELEASE",
      "swiftwasm-build": "8ee6bfafa7a114347e3250da2131c8436b4e7a58"
    }
  },
  "swift-sdks": {
    "wasm32-unknown-wasi": {
      "id": "6.0.3-RELEASE-wasm32-unknown-wasi",
      "url": "https://github.com/swiftwasm/swift/releases/download/swift-wasm-6.0.3-RELEASE/swift-wasm-6.0.3-RELEASE-wasm32-unknown-wasi.artifactbundle.zip",
      "checksum": "31d3585b06dd92de390bacc18527801480163188cd7473f492956b5e213a8618"
    }
  }
}
```

## Example usage

### Get the release tag for the currently selected toolchain

```console
$ curl -sL "https://raw.githubusercontent.com/swiftwasm/swift-sdk-index/refs/heads/main/v1/tag-by-version.json" | jq --arg v "$(swiftc --version | head -n1)" '.[$v]'
[
  "swift-6.0.3-RELEASE"
]
```

### Install correct Swift SDK for the currently selected toolchain

```console
$ (
  V="$(swiftc --version | head -n1)"; \
  TAG="$(curl -sL "https://raw.githubusercontent.com/swiftwasm/swift-sdk-index/refs/heads/main/v1/tag-by-version.json" | jq -r --arg v "$V" '.[$v] | .[-1]')"; \
  curl -sL "https://raw.githubusercontent.com/swiftwasm/swift-sdk-index/refs/heads/main/v1/builds/$TAG.json" | \
  jq -r '.["swift-sdks"]["wasm32-unknown-wasi"] | "swift sdk install \"\(.url)\" --checksum \"\(.checksum)\""' | sh -x
)
```
