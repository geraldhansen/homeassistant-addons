# S3 Backup Add-on

A comprehensive Home Assistant add-on for backing up your Home Assistant instance to Amazon S3 (or compatible storage services).

## Features

- **Web Interface**: Beautiful, modern web UI for managing backups
- **Automatic Uploads**: Automatically upload new backups to S3
- **S3 Compatible**: Works with Amazon S3, MinIO, DigitalOcean Spaces, and other S3-compatible services
- **Backup Management**: Create, upload, and manage backups through the web interface
- **Real-time Status**: Live status updates and connection monitoring
- **Flexible Storage**: Support for different S3 storage classes (Standard, IA, Glacier, etc.)
- **Local Cleanup**: Optionally delete old local backups to save space

## Web Interface

The add-on includes a modern web interface with the following pages:

### Dashboard
- Overview of local and S3 backups
- System status and statistics
- Quick backup creation
- Real-time connection status

### Backups
- Detailed backup management
- Upload backups to S3
- Download backups from S3
- Delete old backups
- Backup details and metadata

### Settings
- S3 configuration
- Connection testing
- Backup policies
- Auto-save functionality

## Configuration

Configure the add-on through either the Home Assistant add-on configuration or the built-in web interface:

```yaml
s3_bucket: "your-backup-bucket"
s3_region: "us-east-1"
s3_access_key: "your-access-key"
s3_secret_key: "your-secret-key"
s3_prefix: "ha-backups/"
endpoint_url: ""  # Optional: for S3-compatible services
delete_local_backups: true
local_backups_to_keep: 4
```

## Installation

1. Add this repository to your Home Assistant add-on store
2. Install the "S3 Backup" add-on
3. Configure your S3 credentials
4. Start the add-on
5. Open the web UI to manage your backups

## S3 Compatible Services

This add-on works with various S3-compatible services:

- Amazon S3
- MinIO
- DigitalOcean Spaces
- Wasabi
- Backblaze B2 (with S3-compatible API)
- Any S3-compatible storage service

## Support

For issues and feature requests, please use the GitHub repository.

## Local Development

### Prerequisites

- [VS Code](https://code.visualstudio.com/)
- [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) (`ms-vscode-remote.remote-containers`)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### First-time setup

1. Open this folder in VS Code
2. When prompted, click **Reopen in Container** — or use the Command Palette (`Cmd+Shift+P`) → **Dev Containers: Reopen in Container**
3. Wait for the container to build (pulls `ghcr.io/home-assistant/devcontainer:addons`)

### Starting Home Assistant

After the container is running:

- **Terminal → Run Task → Start Home Assistant**, or
- Press `Cmd+Shift+P` → **Tasks: Run Test Task**

Home Assistant will be available at **http://localhost:7123/**

Your add-on appears automatically under **Settings → Add-ons → Local add-ons**.

### Notes

- Port `7123` is used instead of the default `8123` to avoid conflicts with a local Home Assistant instance
- The devcontainer image supports both `amd64` and `arm64` — Apple Silicon works natively
- To force a local build instead of pulling a published image, comment out the `image:` key in `config.yaml`
