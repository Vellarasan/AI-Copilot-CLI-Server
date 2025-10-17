"""
GitHub Copilot CLI API Server
Exposes API endpoints to trigger Copilot code generation and Git operations
"""

import logging
import os
import subprocess
from datetime import datetime

from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
REPOS_BASE_PATH = os.getenv('REPOS_BASE_PATH', '/var/repos')
ALLOWED_REPOS = os.getenv('ALLOWED_REPOS', '').split(',')  # Whitelist of allowed repos


class CopilotExecutor:
    """Handles GitHub Copilot CLI execution and Git operations"""
    
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        
    def validate_repo(self):
        """Validate that the repository exists and is a git repo"""
        if not os.path.exists(self.repo_path):
            raise ValueError(f"Repository path does not exist: {self.repo_path}")
        
        git_dir = os.path.join(self.repo_path, '.git')
        if not os.path.exists(git_dir):
            raise ValueError(f"Not a git repository: {self.repo_path}")
    
    def run_command(self, command: list, cwd: str = None) -> dict:
        """Execute a shell command and return result"""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.repo_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': 'Command timed out after 5 minutes',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }
    
    def execute_copilot(self, prompt: str, files: list = None) -> dict:
        """Execute GitHub Copilot CLI with the given prompt"""
        logger.info(f"Executing Copilot with prompt: {prompt}")
        
        # Build the copilot command
        # Note: Adjust this based on actual GitHub Copilot CLI syntax
        command = ['gh', 'copilot', 'suggest']
        
        if files:
            command.extend(['--files', ','.join(files)])
        
        command.append(prompt)
        
        result = self.run_command(command)
        
        if result['success']:
            logger.info("Copilot execution successful")
        else:
            logger.error(f"Copilot execution failed: {result['stderr']}")
        
        return result
    
    def git_status(self) -> dict:
        """Get git status"""
        return self.run_command(['git', 'status', '--porcelain'])
    
    def git_add(self, files: list = None) -> dict:
        """Stage files for commit"""
        if files:
            command = ['git', 'add'] + files
        else:
            command = ['git', 'add', '-A']
        
        return self.run_command(command)
    
    def git_commit(self, message: str) -> dict:
        """Commit staged changes"""
        return self.run_command(['git', 'commit', '-m', message])
    
    def git_push(self, branch: str = None, remote: str = 'origin') -> dict:
        """Push commits to remote"""
        command = ['git', 'push', remote]
        if branch:
            command.append(branch)
        
        return self.run_command(command)
    
    def git_checkout_branch(self, branch: str, create: bool = False) -> dict:
        """Checkout or create a branch"""
        command = ['git', 'checkout']
        if create:
            command.append('-b')
        command.append(branch)
        
        return self.run_command(command)


def validate_request(data: dict) -> tuple:
    """Validate incoming request data"""
    repo_name = data.get('repo_name')
    
    if not repo_name:
        return False, "repo_name is required"
    
    # Check if repo is in whitelist (if configured)
    if ALLOWED_REPOS and ALLOWED_REPOS[0] and repo_name not in ALLOWED_REPOS:
        return False, f"Repository {repo_name} is not allowed"
    
    return True, None


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


@app.route('/api/copilot/execute', methods=['POST'])
def execute_copilot():
    """
    Execute GitHub Copilot CLI
    
    Request body:
    {
        "repo_name": "my-repo",
        "prompt": "Add error handling to the API",
        "files": ["src/api.py"] (optional)
    }
    """
    try:
        data = request.get_json()
        
        # Validate request
        is_valid, error_msg = validate_request(data)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        repo_name = data['repo_name']
        prompt = data.get('prompt')
        files = data.get('files', [])
        
        if not prompt:
            return jsonify({'error': 'prompt is required'}), 400
        
        # Build repo path
        repo_path = os.path.join(REPOS_BASE_PATH, repo_name)
        
        # Execute Copilot
        executor = CopilotExecutor(repo_path)
        executor.validate_repo()
        
        result = executor.execute_copilot(prompt, files)
        
        # Get git status to show what changed
        status = executor.git_status()
        
        return jsonify({
            'success': result['success'],
            'output': result['stdout'],
            'error': result['stderr'],
            'git_status': status['stdout'],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.exception("Error executing Copilot")
        return jsonify({'error': str(e)}), 500


@app.route('/api/git/commit-and-push', methods=['POST'])
def commit_and_push():
    """
    Commit and push changes
    
    Request body:
    {
        "repo_name": "my-repo",
        "commit_message": "Add feature X",
        "branch": "main" (optional),
        "files": ["src/api.py"] (optional, defaults to all changes)
    }
    """
    try:
        data = request.get_json()
        
        # Validate request
        is_valid, error_msg = validate_request(data)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        repo_name = data['repo_name']
        commit_message = data.get('commit_message')
        branch = data.get('branch')
        files = data.get('files')
        
        if not commit_message:
            return jsonify({'error': 'commit_message is required'}), 400
        
        # Build repo path
        repo_path = os.path.join(REPOS_BASE_PATH, repo_name)
        
        # Execute Git operations
        executor = CopilotExecutor(repo_path)
        executor.validate_repo()
        
        results = {}
        
        # Add files
        add_result = executor.git_add(files)
        results['add'] = add_result
        
        if not add_result['success']:
            return jsonify({
                'error': 'Failed to stage files',
                'details': add_result['stderr']
            }), 500
        
        # Commit
        commit_result = executor.git_commit(commit_message)
        results['commit'] = commit_result
        
        if not commit_result['success']:
            return jsonify({
                'error': 'Failed to commit',
                'details': commit_result['stderr']
            }), 500
        
        # Push
        push_result = executor.git_push(branch)
        results['push'] = push_result
        
        if not push_result['success']:
            return jsonify({
                'error': 'Failed to push',
                'details': push_result['stderr']
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Changes committed and pushed successfully',
            'results': {
                'add': add_result['stdout'],
                'commit': commit_result['stdout'],
                'push': push_result['stdout']
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.exception("Error committing and pushing")
        return jsonify({'error': str(e)}), 500


@app.route('/api/workflow/copilot-commit-push', methods=['POST'])
def copilot_commit_push_workflow():
    """
    Complete workflow: Execute Copilot, commit, and push
    
    Request body:
    {
        "repo_name": "my-repo",
        "prompt": "Add error handling",
        "commit_message": "Add error handling to API",
        "branch": "main" (optional),
        "files": ["src/api.py"] (optional)
    }
    """
    try:
        data = request.get_json()
        
        # Validate request
        is_valid, error_msg = validate_request(data)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        repo_name = data['repo_name']
        prompt = data.get('prompt')
        commit_message = data.get('commit_message')
        branch = data.get('branch')
        files = data.get('files')
        
        if not prompt:
            return jsonify({'error': 'prompt is required'}), 400
        if not commit_message:
            return jsonify({'error': 'commit_message is required'}), 400
        
        # Build repo path
        repo_path = os.path.join(REPOS_BASE_PATH, repo_name)
        
        executor = CopilotExecutor(repo_path)
        executor.validate_repo()
        
        workflow_results = {}
        
        # Step 1: Execute Copilot
        logger.info("Step 1: Executing Copilot")
        copilot_result = executor.execute_copilot(prompt, files)
        workflow_results['copilot'] = copilot_result
        
        if not copilot_result['success']:
            return jsonify({
                'error': 'Copilot execution failed',
                'details': copilot_result['stderr'],
                'workflow_results': workflow_results
            }), 500
        
        # Step 2: Add files
        logger.info("Step 2: Staging changes")
        add_result = executor.git_add(files)
        workflow_results['add'] = add_result
        
        if not add_result['success']:
            return jsonify({
                'error': 'Failed to stage files',
                'details': add_result['stderr'],
                'workflow_results': workflow_results
            }), 500
        
        # Step 3: Commit
        logger.info("Step 3: Committing changes")
        commit_result = executor.git_commit(commit_message)
        workflow_results['commit'] = commit_result
        
        if not commit_result['success']:
            return jsonify({
                'error': 'Failed to commit',
                'details': commit_result['stderr'],
                'workflow_results': workflow_results
            }), 500
        
        # Step 4: Push
        logger.info("Step 4: Pushing changes")
        push_result = executor.git_push(branch)
        workflow_results['push'] = push_result
        
        if not push_result['success']:
            return jsonify({
                'error': 'Failed to push',
                'details': push_result['stderr'],
                'workflow_results': workflow_results
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Copilot workflow completed successfully',
            'workflow_results': workflow_results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.exception("Error in Copilot workflow")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Create repos directory if it doesn't exist
    os.makedirs(REPOS_BASE_PATH, exist_ok=True)
    
    # Run the server
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)