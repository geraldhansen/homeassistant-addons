# Home Assistant Add-on: S3 Backup

A comprehensive Home Assistant add-on for backing up your Home Assistant instance to Amazon S3 or compatible storage services, featuring a modern web interface.

## Installation

Follow these steps to get the add-on installed on your system:

1. Enable **Advanced Mode** in your Home Assistant user profile.
2. Navigate in your Home Assistant frontend to **Settings** -> **Add-ons** -> **ADD-ON STORE**.
3. Add this url as new repository url "https://github.com/geraldhansen/homeassistant-addons"
4. Search for "S3 Backup" add-on and click on it.
5. Click **Install** to install the add-on.
6. Configure the add-on (see configuration section below).
7. Click **Start** to start the add-on.
8. Click **Open Web UI** to access the management interface.

## Web Interface

This add-on features a comprehensive web interface with three main sections:

### Dashboard
- Overview of local and S3 backups
- System status and statistics
- Quick backup creation
- Real-time connection status monitoring

### Backups
- Detailed backup management with tabbed interface
- Upload local backups to S3
- Download backups from S3
- View backup details and metadata
- Delete old backups from either location

### Settings
- Configure S3 credentials and settings
- Test S3 connection before saving
- Auto-save functionality
- Built-in help and documentation
4. Click on the "INSTALL" button.

## How to use

1. Set the `aws_access_key`, `aws_secret_access_key`, and `bucket_name`. 
2. Optionally / if necessary, change `bucket_region`, `storage_class`, and `delete_local_backups` and `local_backups_to_keep` configuration options.
3. Start the add-on. It runs continuously and syncs your backups to the configured `bucket_name` automatically (checked hourly), so no Home Assistant automation is needed.

## Encryption key (important)

Home Assistant encrypts your backups. Without the encryption key you **cannot restore** them, even though they are safely stored in S3. Save the key somewhere safe and outside of Home Assistant:

- **Settings** -> **System** -> **Backup** -> **Show my encryption key**, or
- **Settings** -> **System** -> **Backup** -> **Download emergency kit**

For details, see the [Home Assistant emergency kit documentation](https://www.home-assistant.io/more-info/backup-emergency-kit).

## Configuration

Example add-on configuration:

```
aws_access_key_id: AKXXXXXXXXXXXXXXXX
aws_secret_access_key: XXXXXXXXXXXXXXXX
bucket_name: my-bucket
endpoint_url: https://us-east-1.amazonaws.com
delete_local_backups: true
local_backups_to_keep: 3
```

### Option: `aws_access_key_id` (required)
Access key id used to access the S3 bucket.

### Option: `aws_secret_access_key` (required)
Secret access key used to access the S3 bucket.

### Option: `bucket_name` (required)
S3 bucket name used to store backups.

### Option: `endpoint_url` (optional)
S3 endpoint url for your provider

### Option: `bucket_region` (optional, Default: eu-central-1)
Region where the S3 bucket was created. See https://aws.amazon.com/about-aws/global-infrastructure/ for all available regions.

### Option: `storage_class` (optional, Default: STANDARD)
Amazon S3 storage class to use for the synced objects, when uploading files to S3. One of STANDARD, REDUCED_REDUNDANCY, STANDARD_IA, ONEZONE_IA, INTELLIGENT_TIERING, GLACIER, DEEP_ARCHIVE. For more information see https://aws.amazon.com/s3/storage-classes/.

### Option: `delete_local_backups` (optional, Default: true)
Should the addon remove oldest local backups after syncing to your Amazon S3 Bucket? You can configure how many local backups you want to keep with the Option `local_backups_to_keep`. Oldest Backups will get deleted first.

### Option: `local_backups_to_keep` (optional, Default: 4)
How many backups you want to keep locally? If you want to disable automatic local cleanup, set `delete_local_backups` to false.

If you also want to automatically delete backups to keep your Amazon S3 Bucket clean, or change the storage class for backups to safe some money, you should take a look at S3 Lifecycle Rules (https://docs.aws.amazon.com/AmazonS3/latest/userguide/how-to-set-lifecycle-configuration-intro.html).

## Security
I recommend to create a new IAM user, which:
- can not login to the AWS Console
- can only access AWS programmatically
- is used by this add-on only
- uses the lowest possible IAM Policy, which is this:

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowAWSS3Sync",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::YOUR-S3-BUCKET-NAME/*",
                "arn:aws:s3:::YOUR-S3-BUCKET-NAME"
            ]
        }
    ]
}
```

## Support

Usage of the addon requires knowledge of Amazon S3 and AWS IAM.
Under the hood it uses the aws cli version 1, specifically the `aws s3 sync` command.

## Thanks
This addon is highly inspired by https://github.com/thomasfr/hass-addons  
[Bucket Icon](https://iconscout.com/icons/bucket) by [Daniel Bruce](https://iconscout.com/contributors/daniel-bruce")
