#!/usr/bin/env python3
import sys
import json
import logging
import subprocess

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GitHubSecretsCopier:
    def __init__(self):
        self.source_repo = "Arnarsson/crewai"
        self.target_repo = "Arnarsson/agentz"
        self.environments = ["staging", "production", "test"]
    
    def list_secrets(self, repo, environment=None):
        """List secrets using GitHub API."""
        try:
            if environment:
                cmd = ["gh", "api", f"/repos/{repo}/environments/{environment}/secrets", "--jq", ".secrets[].name"]
            else:
                cmd = ["gh", "api", f"/repos/{repo}/actions/secrets", "--jq", ".secrets[].name"]
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return [s.strip() for s in result.stdout.splitlines() if s.strip()]
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list secrets for {repo} {environment}: {e.stderr}")
            raise
    
    def copy_secret(self, secret_name, environment=None):
        """Copy a secret from source to target repo."""
        try:
            # Get secret value from source repo using environment variable
            env_prefix = f"{environment.upper()}_" if environment else ""
            env_var = f"{env_prefix}{secret_name}"
            
            # Set secret in target repo
            set_cmd = ["gh", "secret", "set", secret_name, "-R", self.target_repo]
            if environment:
                set_cmd.extend(["--env", environment])
            set_cmd.extend(["-b", env_var])
            
            subprocess.run(set_cmd, check=True, capture_output=True)
            logger.info(f"Copied secret {secret_name} to {self.target_repo} {environment if environment else 'repo-level'}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to copy secret {secret_name}: {e.stderr}")
            raise
    
    def run(self):
        """Run the secrets copying process."""
        try:
            # Copy secrets for each environment
            for env in self.environments:
                logger.info(f"\nProcessing environment: {env}")
                env_secrets = self.list_secrets(self.source_repo, env)
                for secret in env_secrets:
                    self.copy_secret(secret, env)
                
            logger.info("\nAll secrets copied successfully!")
            
        except Exception as e:
            logger.error(f"Failed to copy secrets: {str(e)}")
            raise

def main():
    try:
        copier = GitHubSecretsCopier()
        copier.run()
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 