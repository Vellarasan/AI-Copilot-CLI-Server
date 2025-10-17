"""
Python Client Library for GitHub Copilot API Server
Simplifies interaction with the Copilot API
"""

import requests
from typing import Optional, List, Dict
import json


class CopilotAPIClient:
    """Client for interacting with the GitHub Copilot API Server"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """
        Initialize the client
        
        Args:
            base_url: Base URL of the API server (e.g., http://localhost:5000)
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({'X-API-Key': api_key})
        
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def health_check(self) -> Dict:
        """
        Check if the API server is healthy
        
        Returns:
            dict: Health status response
        """
        response = self.session.get(f'{self.base_url}/health')
        response.raise_for_status()
        return response.json()
    
    def execute_copilot(
        self,
        repo_name: str,
        prompt: str,
        files: Optional[List[str]] = None
    ) -> Dict:
        """
        Execute GitHub Copilot CLI on the server
        
        Args:
            repo_name: Name of the repository
            prompt: Copilot prompt describing the desired code changes
            files: Optional list of specific files to target
        
        Returns:
            dict: Copilot execution result
        
        Raises:
            requests.HTTPError: If the request fails
        """
        payload = {
            'repo_name': repo_name,
            'prompt': prompt
        }
        
        if files:
            payload['files'] = files
        
        response = self.session.post(
            f'{self.base_url}/api/copilot/execute',
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def commit_and_push(
        self,
        repo_name: str,
        commit_message: str,
        branch: Optional[str] = None,
        files: Optional[List[str]] = None
    ) -> Dict:
        """
        Commit and push changes to the repository
        
        Args:
            repo_name: Name of the repository
            commit_message: Git commit message
            branch: Optional branch name (defaults to current branch)
            files: Optional list of specific files to commit
        
        Returns:
            dict: Git operation results
        
        Raises:
            requests.HTTPError: If the request fails
        """
        payload = {
            'repo_name': repo_name,
            'commit_message': commit_message
        }
        
        if branch:
            payload['branch'] = branch
        
        if files:
            payload['files'] = files
        
        response = self.session.post(
            f'{self.base_url}/api/git/commit-and-push',
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def copilot_workflow(
        self,
        repo_name: str,
        prompt: str,
        commit_message: str,
        branch: Optional[str] = None,
        files: Optional[List[str]] = None
    ) -> Dict:
        """
        Execute complete workflow: Copilot generation + commit + push
        
        Args:
            repo_name: Name of the repository
            prompt: Copilot prompt describing the desired code changes
            commit_message: Git commit message
            branch: Optional branch name
            files: Optional list of specific files to target
        
        Returns:
            dict: Complete workflow results
        
        Raises:
            requests.HTTPError: If the request fails
        """
        payload = {
            'repo_name': repo_name,
            'prompt': prompt,
            'commit_message': commit_message
        }
        
        if branch:
            payload['branch'] = branch
        
        if files:
            payload['files'] = files
        
        response = self.session.post(
            f'{self.base_url}/api/workflow/copilot-commit-push',
            json=payload
        )
        response.raise_for_status()
        return response.json()


# Example usage
if __name__ == '__main__':
    # Initialize client
    client = CopilotAPIClient(
        base_url='http://localhost:5000',
        api_key='your-api-key'  # Optional
    )
    
    # Check server health
    try:
        health = client.health_check()
        print(f"Server status: {health}")
    except Exception as e:
        print(f"Server is not reachable: {e}")
        exit(1)
    
    # Example 1: Execute Copilot only
    print("\n--- Example 1: Execute Copilot ---")
    try:
        result = client.execute_copilot(
            repo_name='my-project',
            prompt='Add input validation to user registration',
            files=['src/auth.py']
        )
        print(f"Success: {result['success']}")
        print(f"Output: {result['output']}")
    except requests.HTTPError as e:
        print(f"Error: {e.response.json()}")
    
    # Example 2: Commit and push existing changes
    print("\n--- Example 2: Commit and Push ---")
    try:
        result = client.commit_and_push(
            repo_name='my-project',
            commit_message='Add validation to auth module',
            branch='main'
        )
        print(f"Success: {result['success']}")
        print(f"Message: {result['message']}")
    except requests.HTTPError as e:
        print(f"Error: {e.response.json()}")
    
    # Example 3: Complete workflow
    print("\n--- Example 3: Complete Workflow ---")
    try:
        result = client.copilot_workflow(
            repo_name='my-project',
            prompt='Add unit tests for the authentication service',
            commit_message='Add auth service unit tests',
            branch='feature/tests'
        )
        print(f"Success: {result['success']}")
        print(f"Message: {result['message']}")
        
        # Access detailed results
        if 'workflow_results' in result:
            print("\nWorkflow Details:")
            for step, step_result in result['workflow_results'].items():
                print(f"  {step}: {'✓' if step_result['success'] else '✗'}")
    except requests.HTTPError as e:
        print(f"Error: {e.response.json()}")