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
aws_access_key_id: "your-access-key"
aws_secret_access_key: "your-secret-key"
bucket_name: "your-backup-bucket"
endpoint_url: ""  # Optional: for S3-compatible services
bucket_region: "us-east-1"
storage_class: "STANDARD"
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