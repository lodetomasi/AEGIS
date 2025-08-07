"""Environment simulation for AEGIS testing."""

import copy
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json
import random
from datetime import datetime


@dataclass
class EnvironmentState:
    """Represents the state of a simulated environment."""
    
    id: str
    type: str
    state: Dict[str, Any]
    history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def snapshot(self) -> Dict[str, Any]:
        """Create a snapshot of current state."""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'state': copy.deepcopy(self.state),
            'metadata': copy.deepcopy(self.metadata)
        }
    
    def record_change(self, action: str, changes: Dict[str, Any]):
        """Record a state change."""
        self.history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'changes': changes,
            'state_after': self.snapshot()
        })


class MockEnvironment(ABC):
    """Base class for mock environments."""
    
    def __init__(self, env_id: str, initial_state: Optional[Dict[str, Any]] = None):
        self.env_id = env_id
        self.initial_state = initial_state or self.get_default_state()
        self.state = EnvironmentState(
            id=env_id,
            type=self.__class__.__name__,
            state=copy.deepcopy(self.initial_state)
        )
        self.callbacks: Dict[str, List[Callable]] = {}
    
    @abstractmethod
    def get_default_state(self) -> Dict[str, Any]:
        """Get default initial state."""
        pass
    
    def reset(self):
        """Reset environment to initial state."""
        self.state.state = copy.deepcopy(self.initial_state)
        self.state.history.clear()
    
    def get_state(self) -> Dict[str, Any]:
        """Get current state."""
        return copy.deepcopy(self.state.state)
    
    def set_state(self, new_state: Dict[str, Any]):
        """Set environment state."""
        old_state = self.state.state
        self.state.state = copy.deepcopy(new_state)
        self.state.record_change("set_state", {
            'old': old_state,
            'new': new_state
        })
    
    def register_callback(self, event: str, callback: Callable):
        """Register callback for environment events."""
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
    
    def trigger_event(self, event: str, data: Any = None):
        """Trigger environment event."""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                callback(self, data)


class MockDatabase(MockEnvironment):
    """Simulated database environment."""
    
    def get_default_state(self) -> Dict[str, Any]:
        return {
            'tables': {
                'users': [
                    {'id': 1, 'name': 'Alice', 'email': 'alice@example.com', 'role': 'admin'},
                    {'id': 2, 'name': 'Bob', 'email': 'bob@example.com', 'role': 'user'},
                    {'id': 3, 'name': 'Charlie', 'email': 'charlie@example.com', 'role': 'user'}
                ],
                'products': [
                    {'id': 1, 'name': 'Widget A', 'price': 29.99, 'stock': 100},
                    {'id': 2, 'name': 'Widget B', 'price': 49.99, 'stock': 50},
                    {'id': 3, 'name': 'Widget C', 'price': 99.99, 'stock': 25}
                ],
                'orders': []
            },
            'indexes': {
                'users_email': {'alice@example.com': 1, 'bob@example.com': 2, 'charlie@example.com': 3},
                'products_name': {'Widget A': 1, 'Widget B': 2, 'Widget C': 3}
            }
        }
    
    def query(self, table: str, conditions: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a query on the database."""
        if table not in self.state.state['tables']:
            raise ValueError(f"Table '{table}' does not exist")
        
        results = self.state.state['tables'][table]
        
        if conditions:
            results = [
                row for row in results
                if all(row.get(k) == v for k, v in conditions.items())
            ]
        
        self.trigger_event('query', {'table': table, 'conditions': conditions, 'results': len(results)})
        return copy.deepcopy(results)
    
    def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert data into table."""
        if table not in self.state.state['tables']:
            raise ValueError(f"Table '{table}' does not exist")
        
        # Auto-increment ID
        max_id = max([r.get('id', 0) for r in self.state.state['tables'][table]], default=0)
        data['id'] = max_id + 1
        
        self.state.state['tables'][table].append(data)
        self.state.record_change('insert', {'table': table, 'data': data})
        self.trigger_event('insert', {'table': table, 'data': data})
        
        return data
    
    def update(self, table: str, conditions: Dict[str, Any], updates: Dict[str, Any]) -> int:
        """Update records in table."""
        if table not in self.state.state['tables']:
            raise ValueError(f"Table '{table}' does not exist")
        
        count = 0
        for row in self.state.state['tables'][table]:
            if all(row.get(k) == v for k, v in conditions.items()):
                row.update(updates)
                count += 1
        
        self.state.record_change('update', {
            'table': table,
            'conditions': conditions,
            'updates': updates,
            'affected': count
        })
        self.trigger_event('update', {'table': table, 'count': count})
        
        return count
    
    def delete(self, table: str, conditions: Dict[str, Any]) -> int:
        """Delete records from table."""
        if table not in self.state.state['tables']:
            raise ValueError(f"Table '{table}' does not exist")
        
        original_count = len(self.state.state['tables'][table])
        self.state.state['tables'][table] = [
            row for row in self.state.state['tables'][table]
            if not all(row.get(k) == v for k, v in conditions.items())
        ]
        
        deleted = original_count - len(self.state.state['tables'][table])
        
        self.state.record_change('delete', {
            'table': table,
            'conditions': conditions,
            'deleted': deleted
        })
        self.trigger_event('delete', {'table': table, 'count': deleted})
        
        return deleted


class MockFileSystem(MockEnvironment):
    """Simulated file system environment."""
    
    def get_default_state(self) -> Dict[str, Any]:
        return {
            'files': {
                '/home/user/document.txt': {
                    'content': 'This is a test document.',
                    'permissions': 'rw-r--r--',
                    'owner': 'user',
                    'size': 24,
                    'modified': datetime.utcnow().isoformat()
                },
                '/home/user/data.json': {
                    'content': '{"key": "value", "items": [1, 2, 3]}',
                    'permissions': 'rw-r--r--',
                    'owner': 'user',
                    'size': 36,
                    'modified': datetime.utcnow().isoformat()
                },
                '/etc/config.ini': {
                    'content': '[settings]\ndebug=false\nport=8080',
                    'permissions': 'r--r--r--',
                    'owner': 'root',
                    'size': 33,
                    'modified': datetime.utcnow().isoformat()
                }
            },
            'directories': {
                '/': {'permissions': 'rwxr-xr-x', 'owner': 'root'},
                '/home': {'permissions': 'rwxr-xr-x', 'owner': 'root'},
                '/home/user': {'permissions': 'rwxr-xr-x', 'owner': 'user'},
                '/etc': {'permissions': 'rwxr-xr-x', 'owner': 'root'},
                '/tmp': {'permissions': 'rwxrwxrwt', 'owner': 'root'}
            }
        }
    
    def read_file(self, path: str) -> str:
        """Read file content."""
        if path not in self.state.state['files']:
            raise FileNotFoundError(f"File not found: {path}")
        
        self.trigger_event('read', {'path': path})
        return self.state.state['files'][path]['content']
    
    def write_file(self, path: str, content: str, create: bool = True):
        """Write content to file."""
        if path not in self.state.state['files'] and not create:
            raise FileNotFoundError(f"File not found: {path}")
        
        file_data = {
            'content': content,
            'permissions': 'rw-r--r--',
            'owner': 'user',
            'size': len(content),
            'modified': datetime.utcnow().isoformat()
        }
        
        if path in self.state.state['files']:
            old_content = self.state.state['files'][path]['content']
            self.state.state['files'][path] = file_data
            self.state.record_change('write', {'path': path, 'old_content': old_content})
        else:
            self.state.state['files'][path] = file_data
            self.state.record_change('create', {'path': path})
        
        self.trigger_event('write', {'path': path, 'size': len(content)})
    
    def delete_file(self, path: str):
        """Delete a file."""
        if path not in self.state.state['files']:
            raise FileNotFoundError(f"File not found: {path}")
        
        del self.state.state['files'][path]
        self.state.record_change('delete', {'path': path})
        self.trigger_event('delete', {'path': path})
    
    def list_directory(self, path: str) -> List[str]:
        """List directory contents."""
        if path not in self.state.state['directories']:
            raise FileNotFoundError(f"Directory not found: {path}")
        
        contents = []
        path_with_slash = path if path.endswith('/') else path + '/'
        
        # Find all files and subdirectories
        for file_path in self.state.state['files']:
            if file_path.startswith(path_with_slash):
                relative = file_path[len(path_with_slash):]
                if '/' not in relative:
                    contents.append(relative)
        
        for dir_path in self.state.state['directories']:
            if dir_path != path and dir_path.startswith(path_with_slash):
                relative = dir_path[len(path_with_slash):].rstrip('/')
                if '/' not in relative:
                    contents.append(relative + '/')
        
        self.trigger_event('list', {'path': path})
        return sorted(contents)


class MockAPIEndpoint(MockEnvironment):
    """Simulated API endpoint."""
    
    def get_default_state(self) -> Dict[str, Any]:
        return {
            'endpoints': {
                '/api/users': {
                    'GET': {'status': 200, 'data': [{'id': 1, 'name': 'User 1'}]},
                    'POST': {'status': 201, 'data': {'id': 2, 'name': 'New User'}}
                },
                '/api/auth': {
                    'POST': {'status': 200, 'data': {'token': 'mock-jwt-token'}}
                }
            },
            'rate_limits': {
                'requests_per_minute': 60,
                'current_requests': 0
            },
            'auth_tokens': ['mock-jwt-token', 'test-token-123']
        }
    
    def call(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None, 
             headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make API call."""
        # Check rate limit
        if self.state.state['rate_limits']['current_requests'] >= self.state.state['rate_limits']['requests_per_minute']:
            return {'status': 429, 'error': 'Rate limit exceeded'}
        
        self.state.state['rate_limits']['current_requests'] += 1
        
        # Check authentication
        if headers and 'Authorization' in headers:
            token = headers['Authorization'].replace('Bearer ', '')
            if token not in self.state.state['auth_tokens']:
                return {'status': 401, 'error': 'Invalid token'}
        
        # Get endpoint response
        if endpoint in self.state.state['endpoints']:
            if method in self.state.state['endpoints'][endpoint]:
                response = copy.deepcopy(self.state.state['endpoints'][endpoint][method])
                self.trigger_event('api_call', {
                    'method': method,
                    'endpoint': endpoint,
                    'data': data,
                    'response': response
                })
                return response
        
        return {'status': 404, 'error': 'Endpoint not found'}


class EnvironmentSimulator:
    """Manages multiple simulated environments for testing."""
    
    def __init__(self):
        self.environments: Dict[str, MockEnvironment] = {}
        self.active_environment: Optional[str] = None
    
    def create_environment(self, env_type: str, env_id: str, 
                         initial_state: Optional[Dict[str, Any]] = None) -> MockEnvironment:
        """Create a new environment."""
        env_classes = {
            'database': MockDatabase,
            'filesystem': MockFileSystem,
            'api': MockAPIEndpoint
        }
        
        if env_type not in env_classes:
            raise ValueError(f"Unknown environment type: {env_type}")
        
        env = env_classes[env_type](env_id, initial_state)
        self.environments[env_id] = env
        
        if self.active_environment is None:
            self.active_environment = env_id
        
        return env
    
    def get_environment(self, env_id: str) -> MockEnvironment:
        """Get environment by ID."""
        if env_id not in self.environments:
            raise ValueError(f"Environment not found: {env_id}")
        return self.environments[env_id]
    
    def set_active(self, env_id: str):
        """Set active environment."""
        if env_id not in self.environments:
            raise ValueError(f"Environment not found: {env_id}")
        self.active_environment = env_id
    
    def get_active(self) -> MockEnvironment:
        """Get active environment."""
        if self.active_environment is None:
            raise ValueError("No active environment set")
        return self.environments[self.active_environment]
    
    def reset_all(self):
        """Reset all environments."""
        for env in self.environments.values():
            env.reset()
    
    def snapshot_all(self) -> Dict[str, Any]:
        """Create snapshot of all environments."""
        return {
            env_id: env.state.snapshot()
            for env_id, env in self.environments.items()
        }
    
    def restore_snapshot(self, snapshot: Dict[str, Any]):
        """Restore environments from snapshot."""
        for env_id, state_data in snapshot.items():
            if env_id in self.environments:
                self.environments[env_id].set_state(state_data['state'])