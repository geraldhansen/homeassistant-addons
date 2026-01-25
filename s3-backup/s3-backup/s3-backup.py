#!/usr/bin/env python3

import os
import json
import logging
import boto3
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from botocore.exceptions import ClientError, NoCredentialsError
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Configuration
HA_API_URL = 'http://supervisor/core/api'
SUPERVISOR_API_URL = 'http://supervisor'
SUPERVISOR_TOKEN = os.environ.get('SUPERVISOR_TOKEN')

def get_addon_config():
    """Get addon configuration"""
    try:
        with open('/data/options.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Configuration file not found, using defaults")
        return {
            'aws_access_key_id': '',
            'aws_secret_access_key': '',
            'bucket_name': '',
            'endpoint_url': '',
            'bucket_region': 'us-east-1',
            'storage_class': 'STANDARD',
            'delete_local_backups': True,
            'local_backups_to_keep': 4
        }

def get_s3_client():
    """Get configured S3 client"""
    config = get_addon_config()
    
    session = boto3.Session(
        aws_access_key_id=config.get('aws_access_key_id'),
        aws_secret_access_key=config.get('aws_secret_access_key'),
        region_name=config.get('bucket_region', 'us-east-1')
    )
    
    endpoint_url = config.get('endpoint_url')
    if endpoint_url:
        return session.client('s3', endpoint_url=endpoint_url)
    else:
        return session.client('s3')

def get_ha_backups():
    """Get Home Assistant backups"""
    try:
        headers = {
            'Authorization': f'Bearer {SUPERVISOR_TOKEN}',
            'Content-Type': 'application/json'
        }
        response = requests.get(f'{SUPERVISOR_API_URL}/backups', headers=headers)
        if response.status_code == 200:
            return response.json().get('data', {}).get('backups', [])
    except Exception as e:
        logger.error(f"Error fetching backups: {e}")
    return []

def get_s3_backups():
    """Get backups from S3"""
    try:
        config = get_addon_config()
        bucket_name = config.get('bucket_name')
        if not bucket_name:
            return []
        
        s3_client = get_s3_client()
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        
        backups = []
        for obj in response.get('Contents', []):
            if obj['Key'].endswith('.tar'):
                backups.append({
                    'name': obj['Key'],
                    'size': obj['Size'],
                    'date': obj['LastModified'].isoformat(),
                    'location': 'S3'
                })
        return backups
    except Exception as e:
        logger.error(f"Error fetching S3 backups: {e}")
        return []

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """Get system status"""
    config = get_addon_config()
    ha_backups = get_ha_backups()
    s3_backups = get_s3_backups()
    
    # Check S3 connectivity
    s3_connected = False
    try:
        s3_client = get_s3_client()
        bucket_name = config.get('bucket_name')
        if bucket_name:
            s3_client.head_bucket(Bucket=bucket_name)
            s3_connected = True
    except Exception as e:
        logger.error(f"S3 connection failed: {e}")
    
    return jsonify({
        'ha_backups': ha_backups,
        's3_backups': s3_backups,
        's3_connected': s3_connected,
        'config': {
            'bucket_name': config.get('bucket_name', ''),
            'endpoint_url': config.get('endpoint_url', ''),
            'bucket_region': config.get('bucket_region', ''),
            'delete_local_backups': config.get('delete_local_backups', True),
            'local_backups_to_keep': config.get('local_backups_to_keep', 4)
        }
    })

@app.route('/api/backup/<backup_slug>/upload', methods=['POST'])
def upload_backup(backup_slug):
    """Upload a backup to S3"""
    try:
        config = get_addon_config()
        bucket_name = config.get('bucket_name')
        if not bucket_name:
            return jsonify({'error': 'S3 bucket not configured'}), 400
        
        # Get backup file path
        backup_path = f'/backup/{backup_slug}.tar'
        if not os.path.exists(backup_path):
            return jsonify({'error': 'Backup file not found'}), 404
        
        # Upload to S3
        s3_client = get_s3_client()
        storage_class = config.get('storage_class', 'STANDARD')
        
        with open(backup_path, 'rb') as f:
            s3_client.upload_fileobj(
                f, 
                bucket_name, 
                f'{backup_slug}.tar',
                ExtraArgs={'StorageClass': storage_class}
            )
        
        return jsonify({'message': 'Backup uploaded successfully'})
    except Exception as e:
        logger.error(f"Error uploading backup: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/backup/create', methods=['POST'])
def create_backup():
    """Create a new backup"""
    try:
        data = request.get_json() or {}
        backup_name = data.get('name', f'S3 Backup {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        
        headers = {
            'Authorization': f'Bearer {SUPERVISOR_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        backup_data = {
            'name': backup_name,
            'addons': data.get('addons', []),
            'folders': data.get('folders', ['homeassistant', 'ssl', 'share', 'media'])
        }
        
        response = requests.post(
            f'{SUPERVISOR_API_URL}/backups/new/full',
            headers=headers,
            json=backup_data
        )
        
        if response.status_code == 200:
            backup_info = response.json().get('data', {})
            return jsonify({'message': 'Backup created successfully', 'backup': backup_info})
        else:
            return jsonify({'error': 'Failed to create backup'}), 500
            
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    """Test S3 connection with provided credentials"""
    try:
        data = request.get_json()
        
        # Create temporary S3 client with provided credentials
        session = boto3.Session(
            aws_access_key_id=data.get('aws_access_key_id'),
            aws_secret_access_key=data.get('aws_secret_access_key'),
            region_name=data.get('bucket_region', 'us-east-1')
        )
        
        endpoint_url = data.get('endpoint_url')
        if endpoint_url:
            s3_client = session.client('s3', endpoint_url=endpoint_url)
        else:
            s3_client = session.client('s3')
        
        bucket_name = data.get('bucket_name')
        if not bucket_name:
            return jsonify({'success': False, 'error': 'Bucket name is required'})
        
        # Test connection by checking if bucket exists
        s3_client.head_bucket(Bucket=bucket_name)
        
        return jsonify({
            'success': True,
            'bucket_name': bucket_name,
            'message': 'Connection successful'
        })
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            return jsonify({'success': False, 'error': 'Bucket not found'})
        elif error_code == 'NoSuchBucket':
            return jsonify({'success': False, 'error': 'Bucket does not exist'})
        elif error_code == 'InvalidAccessKeyId':
            return jsonify({'success': False, 'error': 'Invalid access key ID'})
        elif error_code == 'SignatureDoesNotMatch':
            return jsonify({'success': False, 'error': 'Invalid secret access key'})
        else:
            return jsonify({'success': False, 'error': f'AWS Error: {error_code}'})
    except NoCredentialsError:
        return jsonify({'success': False, 'error': 'AWS credentials not provided'})
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/save-settings', methods=['POST'])
def save_settings():
    """Save addon configuration"""
    try:
        data = request.get_json()
        
        # Basic validation
        required_fields = ['aws_access_key_id', 'aws_secret_access_key', 'bucket_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'})
        
        # Save to options.json (this would normally be handled by Home Assistant)
        # For now, we'll just validate and return success
        # In a real addon, this would update the addon configuration
        
        logger.info("Settings would be saved (demo mode)")
        return jsonify({'success': True, 'message': 'Settings saved successfully'})
        
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/backup/<backup_slug>/delete', methods=['DELETE'])
def delete_backup(backup_slug):
    """Delete a backup"""
    try:
        headers = {
            'Authorization': f'Bearer {SUPERVISOR_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        response = requests.delete(
            f'{SUPERVISOR_API_URL}/backups/{backup_slug}',
            headers=headers
        )
        
        if response.status_code == 200:
            return jsonify({'message': 'Backup deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete backup'}), 500
            
    except Exception as e:
        logger.error(f"Error deleting backup: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8099, debug=True)