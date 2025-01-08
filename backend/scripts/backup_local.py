#!/usr/bin/env python3
import os
import sys
import shutil
import logging
from datetime import datetime, timedelta
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

class LocalDatabaseBackup:
    def __init__(self):
        self.backup_path = Path(os.getenv('BACKUP_PATH', 'backups'))
        self.backup_path.mkdir(parents=True, exist_ok=True)
        
        # Database configuration
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable is not set")
            
        # Parse database URL
        self.db_info = self._parse_db_url(self.db_url)
        
        # Backup configuration
        self.retention_days = int(os.getenv('BACKUP_RETENTION_DAYS', 30))
        self.compress = os.getenv('BACKUP_COMPRESS', 'true').lower() == 'true'
    
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
        backup_file = self.backup_path / f"backup_{timestamp}.sql"
        
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
            
            # Compress backup if enabled
            if self.compress:
                compressed_file = backup_file.with_suffix('.sql.gz')
                logger.info(f"Compressing backup to: {compressed_file}")
                os.system(f"gzip {backup_file}")
                return compressed_file
            
            return backup_file
            
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            raise
    
    def cleanup_old_backups(self):
        """Clean up old backup files."""
        try:
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            # Get all backup files
            pattern = '*.sql.gz' if self.compress else '*.sql'
            backup_files = list(self.backup_path.glob(pattern))
            
            # Sort files by modification time
            backup_files.sort(key=lambda x: x.stat().st_mtime)
            
            # Remove old files
            for file in backup_files:
                file_time = datetime.fromtimestamp(file.stat().st_mtime)
                if file_time < cutoff_date:
                    logger.info(f"Removing old backup: {file}")
                    file.unlink()
                    
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            raise
    
    def verify_backup(self, backup_file):
        """Verify backup file integrity."""
        try:
            if not backup_file.exists():
                raise Exception(f"Backup file not found: {backup_file}")
            
            # Check file size
            size = backup_file.stat().st_size
            if size == 0:
                raise Exception(f"Backup file is empty: {backup_file}")
            
            logger.info(f"Backup verified: {backup_file} (size: {size} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Backup verification failed: {str(e)}")
            raise

def main():
    try:
        backup = LocalDatabaseBackup()
        backup_file = backup.create_backup()
        backup.verify_backup(backup_file)
        backup.cleanup_old_backups()
        logger.info("Backup completed successfully")
        
    except Exception as e:
        logger.error(f"Backup process failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 