#!/usr/bin/env python3
import os
import sys
import boto3
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class DatabaseBackup:
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # AWS configuration
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        self.bucket_name = os.getenv('BACKUP_S3_BUCKET')
        
        # Database configuration
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable is not set")
            
        # Parse database URL
        self.db_info = self._parse_db_url(self.db_url)
    
    def _parse_db_url(self, url):
        """Parse database URL into components."""
        # Example: postgresql://user:password@localhost:5432/dbname
        parts = url.split('//')
        credentials = parts[1].split('@')[0]
        host_port_db = parts[1].split('@')[1]
        
        user, password = credentials.split(':')
        host_port, dbname = host_port_db.split('/')
        host, port = host_port.split(':')
        
        return {
            'user': user,
            'password': password,
            'host': host,
            'port': port,
            'dbname': dbname
        }
    
    def create_backup(self):
        """Create a database backup."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f"backup_{timestamp}.sql"
        
        try:
            # Create pg_dump command
            cmd = (
                f"PGPASSWORD='{self.db_info['password']}' pg_dump "
                f"-h {self.db_info['host']} "
                f"-p {self.db_info['port']} "
                f"-U {self.db_info['user']} "
                f"-d {self.db_info['dbname']} "
                f"-F p -f {backup_file}"
            )
            
            # Execute backup
            logger.info(f"Creating backup: {backup_file}")
            result = os.system(cmd)
            
            if result != 0:
                raise Exception("Database backup failed")
            
            # Compress backup
            compressed_file = backup_file.with_suffix('.sql.gz')
            os.system(f"gzip {backup_file}")
            
            return compressed_file
            
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            raise
    
    def upload_to_s3(self, backup_file):
        """Upload backup file to S3."""
        try:
            logger.info(f"Uploading {backup_file} to S3")
            self.s3_client.upload_file(
                str(backup_file),
                self.bucket_name,
                f"database_backups/{backup_file.name}"
            )
        except Exception as e:
            logger.error(f"Upload to S3 failed: {str(e)}")
            raise
    
    def cleanup_old_backups(self):
        """Clean up old backup files locally and in S3."""
        try:
            # Clean up local files
            backup_files = sorted(self.backup_dir.glob('*.sql.gz'))
            for file in backup_files[:-5]:  # Keep last 5 backups
                logger.info(f"Removing old backup: {file}")
                file.unlink()
            
            # Clean up S3 files
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix='database_backups/'
            )
            
            if 'Contents' in response:
                objects = sorted(response['Contents'], key=lambda x: x['LastModified'])
                for obj in objects[:-30]:  # Keep last 30 backups in S3
                    logger.info(f"Removing old S3 backup: {obj['Key']}")
                    self.s3_client.delete_object(
                        Bucket=self.bucket_name,
                        Key=obj['Key']
                    )
                    
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            raise

def main():
    try:
        backup = DatabaseBackup()
        backup_file = backup.create_backup()
        backup.upload_to_s3(backup_file)
        backup.cleanup_old_backups()
        logger.info("Backup completed successfully")
        
    except Exception as e:
        logger.error(f"Backup process failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 