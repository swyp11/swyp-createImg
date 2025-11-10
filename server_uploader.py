from pathlib import Path
import paramiko
from typing import Optional
import config


class ServerUploader:
    """Upload files to Linux server via SSH/SFTP"""

    def __init__(self):
        self.ssh_host = config.SSH_HOST
        self.ssh_port = config.SSH_PORT
        self.ssh_user = config.SSH_USER
        self.ssh_password = config.SSH_PASSWORD
        self.server_image_path = config.SERVER_IMAGE_PATH
        self.image_url_base = config.IMAGE_URL_BASE

        if not all([self.ssh_host, self.ssh_user, self.ssh_password]):
            raise ValueError("SSH_HOST, SSH_USER, and SSH_PASSWORD must be set in environment variables")

    def _get_ssh_client(self) -> paramiko.SSHClient:
        """Create and configure SSH client"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            print(f"Connecting to {self.ssh_user}@{self.ssh_host}")
            ssh.connect(
                hostname=self.ssh_host,
                port=self.ssh_port,
                username=self.ssh_user,
                password=self.ssh_password
            )
            return ssh

        except Exception as e:
            print(f"✗ SSH connection failed: {str(e)}")
            raise

    def upload_file(self, local_file_path: Path, table_name: str, filename: str) -> Optional[str]:
        """
        Upload file to server via SFTP

        Args:
            local_file_path: Path to local file
            table_name: Database table name (used as folder name)
            filename: Filename without extension

        Returns:
            URL path for accessing the image, or None if failed
        """
        if not local_file_path.exists():
            print(f"✗ Local file not found: {local_file_path}")
            return None

        ssh = None
        sftp = None

        try:
            ssh = self._get_ssh_client()
            sftp = ssh.open_sftp()

            # Create directory structure: /data/images/{table_name}/
            remote_dir = f"{self.server_image_path}/{table_name}"
            remote_file = f"{remote_dir}/{filename}.png"

            # Create directory if it doesn't exist
            try:
                sftp.stat(remote_dir)
            except FileNotFoundError:
                print(f"Creating directory: {remote_dir}")
                self._create_remote_directory(ssh, remote_dir)

            # Upload file
            print(f"Uploading {local_file_path.name} to {remote_file}")
            sftp.put(str(local_file_path), remote_file)
            print(f"✓ File uploaded successfully")

            # Return URL path: /images/{table_name}/{filename}.png
            url_path = f"{self.image_url_base}/{table_name}/{filename}.png"
            return url_path

        except Exception as e:
            print(f"✗ Upload failed: {str(e)}")
            return None

        finally:
            if sftp:
                sftp.close()
            if ssh:
                ssh.close()

    def _create_remote_directory(self, ssh: paramiko.SSHClient, remote_dir: str):
        """Create directory on remote server with proper permissions"""
        try:
            # Use mkdir -p to create parent directories
            stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {remote_dir}")
            exit_status = stdout.channel.recv_exit_status()

            if exit_status != 0:
                error = stderr.read().decode()
                raise Exception(f"Failed to create directory: {error}")

            # Set permissions (optional)
            ssh.exec_command(f"chmod 755 {remote_dir}")

        except Exception as e:
            print(f"✗ Directory creation failed: {str(e)}")
            raise

    def test_connection(self) -> bool:
        """Test SSH connection to server"""
        try:
            ssh = self._get_ssh_client()
            stdin, stdout, stderr = ssh.exec_command('echo "Connection successful"')
            result = stdout.read().decode().strip()
            ssh.close()

            if result == "Connection successful":
                print("✓ SSH connection test passed")
                return True
            else:
                print("✗ SSH connection test failed")
                return False

        except Exception as e:
            print(f"✗ SSH connection test failed: {str(e)}")
            return False
