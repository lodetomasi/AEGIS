"""
FileSystemStorage: Robust file system storage with atomic operations
"""
import json
import yaml
import csv
import os
import tempfile
import shutil
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import hashlib
from contextlib import contextmanager


class FileSystemStorage:
    """Thread-safe file system storage with atomic operations and write-ahead logging"""
    
    def __init__(self, base_path: str = "./data"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._locks = {}
        self._lock_mutex = threading.Lock()
        self.wal_dir = self.base_path / ".wal"
        self.wal_dir.mkdir(exist_ok=True)
        
    @contextmanager
    def _file_lock(self, path: Path):
        """Acquire file-specific lock for thread safety"""
        with self._lock_mutex:
            if str(path) not in self._locks:
                self._locks[str(path)] = threading.Lock()
            lock = self._locks[str(path)]
        
        lock.acquire()
        try:
            yield
        finally:
            lock.release()
    
    def _write_wal(self, operation: str, path: Path, data: Any = None) -> str:
        """Write-ahead logging for crash recovery"""
        wal_id = f"{datetime.utcnow().isoformat()}_{hashlib.md5(str(path).encode()).hexdigest()}"
        wal_file = self.wal_dir / f"{wal_id}.wal"
        
        wal_entry = {
            "operation": operation,
            "path": str(path),
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        with open(wal_file, 'w') as f:
            json.dump(wal_entry, f)
        
        return wal_id
    
    def _clear_wal(self, wal_id: str):
        """Clear WAL entry after successful operation"""
        wal_file = self.wal_dir / f"{wal_id}.wal"
        if wal_file.exists():
            wal_file.unlink()
    
    def write_json(self, path: Union[str, Path], data: Any, atomic: bool = True) -> bool:
        """Write JSON data atomically"""
        path = Path(path) if isinstance(path, str) else path
        full_path = self.base_path / path if not path.is_absolute() else path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self._file_lock(full_path):
            wal_id = self._write_wal("write_json", full_path, data)
            
            try:
                if atomic:
                    # Write to temporary file first
                    with tempfile.NamedTemporaryFile(
                        mode='w', 
                        dir=full_path.parent, 
                        delete=False,
                        suffix='.tmp'
                    ) as tmp_file:
                        json.dump(data, tmp_file, indent=2, default=str)
                        tmp_path = tmp_file.name
                    
                    # Atomic rename
                    shutil.move(tmp_path, str(full_path))
                else:
                    with open(full_path, 'w') as f:
                        json.dump(data, f, indent=2, default=str)
                
                self._clear_wal(wal_id)
                return True
                
            except Exception as e:
                print(f"Error writing JSON to {full_path}: {e}")
                if atomic and 'tmp_path' in locals() and os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                return False
    
    def read_json(self, path: Union[str, Path]) -> Optional[Any]:
        """Read JSON data safely"""
        path = Path(path) if isinstance(path, str) else path
        full_path = self.base_path / path if not path.is_absolute() else path
        
        if not full_path.exists():
            return None
        
        with self._file_lock(full_path):
            try:
                with open(full_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error reading JSON from {full_path}: {e}")
                return None
    
    def write_yaml(self, path: Union[str, Path], data: Any, atomic: bool = True) -> bool:
        """Write YAML data atomically"""
        path = Path(path) if isinstance(path, str) else path
        full_path = self.base_path / path if not path.is_absolute() else path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self._file_lock(full_path):
            wal_id = self._write_wal("write_yaml", full_path, data)
            
            try:
                if atomic:
                    with tempfile.NamedTemporaryFile(
                        mode='w', 
                        dir=full_path.parent, 
                        delete=False,
                        suffix='.tmp'
                    ) as tmp_file:
                        yaml.dump(data, tmp_file, default_flow_style=False, sort_keys=False)
                        tmp_path = tmp_file.name
                    
                    shutil.move(tmp_path, str(full_path))
                else:
                    with open(full_path, 'w') as f:
                        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
                
                self._clear_wal(wal_id)
                return True
                
            except Exception as e:
                print(f"Error writing YAML to {full_path}: {e}")
                if atomic and 'tmp_path' in locals() and os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                return False
    
    def read_yaml(self, path: Union[str, Path]) -> Optional[Any]:
        """Read YAML data safely"""
        path = Path(path) if isinstance(path, str) else path
        full_path = self.base_path / path if not path.is_absolute() else path
        
        if not full_path.exists():
            return None
        
        with self._file_lock(full_path):
            try:
                with open(full_path, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                print(f"Error reading YAML from {full_path}: {e}")
                return None
    
    def write_csv(self, path: Union[str, Path], data: List[Dict], 
                  fieldnames: Optional[List[str]] = None, atomic: bool = True) -> bool:
        """Write CSV data atomically"""
        path = Path(path) if isinstance(path, str) else path
        full_path = self.base_path / path if not path.is_absolute() else path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not data:
            return False
        
        if not fieldnames:
            fieldnames = list(data[0].keys())
        
        with self._file_lock(full_path):
            wal_id = self._write_wal("write_csv", full_path, {"data": data, "fieldnames": fieldnames})
            
            try:
                if atomic:
                    with tempfile.NamedTemporaryFile(
                        mode='w', 
                        dir=full_path.parent, 
                        delete=False,
                        suffix='.tmp',
                        newline=''
                    ) as tmp_file:
                        writer = csv.DictWriter(tmp_file, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(data)
                        tmp_path = tmp_file.name
                    
                    shutil.move(tmp_path, str(full_path))
                else:
                    with open(full_path, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(data)
                
                self._clear_wal(wal_id)
                return True
                
            except Exception as e:
                print(f"Error writing CSV to {full_path}: {e}")
                if atomic and 'tmp_path' in locals() and os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                return False
    
    def read_csv(self, path: Union[str, Path]) -> Optional[List[Dict]]:
        """Read CSV data safely"""
        path = Path(path) if isinstance(path, str) else path
        full_path = self.base_path / path if not path.is_absolute() else path
        
        if not full_path.exists():
            return None
        
        with self._file_lock(full_path):
            try:
                with open(full_path, 'r', newline='') as f:
                    reader = csv.DictReader(f)
                    return list(reader)
            except Exception as e:
                print(f"Error reading CSV from {full_path}: {e}")
                return None
    
    def append_json_line(self, path: Union[str, Path], data: Any) -> bool:
        """Append JSON line (JSONL format) atomically"""
        path = Path(path) if isinstance(path, str) else path
        full_path = self.base_path / path if not path.is_absolute() else path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self._file_lock(full_path):
            try:
                with open(full_path, 'a') as f:
                    f.write(json.dumps(data, default=str) + '\n')
                return True
            except Exception as e:
                print(f"Error appending to {full_path}: {e}")
                return False
    
    def read_json_lines(self, path: Union[str, Path]) -> Optional[List[Any]]:
        """Read JSONL file"""
        path = Path(path) if isinstance(path, str) else path
        full_path = self.base_path / path if not path.is_absolute() else path
        
        if not full_path.exists():
            return None
        
        with self._file_lock(full_path):
            try:
                lines = []
                with open(full_path, 'r') as f:
                    for line in f:
                        if line.strip():
                            lines.append(json.loads(line.strip()))
                return lines
            except Exception as e:
                print(f"Error reading JSONL from {full_path}: {e}")
                return None
    
    def exists(self, path: Union[str, Path]) -> bool:
        """Check if file exists"""
        path = Path(path) if isinstance(path, str) else path
        full_path = self.base_path / path if not path.is_absolute() else path
        return full_path.exists()
    
    def delete(self, path: Union[str, Path]) -> bool:
        """Delete file safely"""
        path = Path(path) if isinstance(path, str) else path
        full_path = self.base_path / path if not path.is_absolute() else path
        
        with self._file_lock(full_path):
            wal_id = self._write_wal("delete", full_path)
            
            try:
                if full_path.exists():
                    if full_path.is_file():
                        full_path.unlink()
                    else:
                        shutil.rmtree(full_path)
                
                self._clear_wal(wal_id)
                return True
                
            except Exception as e:
                print(f"Error deleting {full_path}: {e}")
                return False
    
    def list_files(self, path: Union[str, Path] = "", pattern: str = "*") -> List[Path]:
        """List files in directory"""
        path = Path(path) if isinstance(path, str) else path
        full_path = self.base_path / path if not path.is_absolute() else path
        
        if not full_path.exists():
            return []
        
        try:
            if full_path.is_dir():
                return list(full_path.glob(pattern))
            else:
                return []
        except Exception as e:
            print(f"Error listing files in {full_path}: {e}")
            return []
    
    def create_checkpoint(self, name: str, paths: List[Union[str, Path]]) -> bool:
        """Create checkpoint of specified files"""
        checkpoint_dir = self.base_path / ".checkpoints" / name
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            for path in paths:
                path = Path(path) if isinstance(path, str) else path
                full_path = self.base_path / path if not path.is_absolute() else path
                
                if full_path.exists():
                    rel_path = full_path.relative_to(self.base_path)
                    dest = checkpoint_dir / rel_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    
                    if full_path.is_file():
                        shutil.copy2(full_path, dest)
                    else:
                        shutil.copytree(full_path, dest, dirs_exist_ok=True)
            
            # Save checkpoint metadata
            metadata = {
                "name": name,
                "timestamp": datetime.utcnow().isoformat(),
                "paths": [str(p) for p in paths]
            }
            
            with open(checkpoint_dir / "metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error creating checkpoint {name}: {e}")
            return False
    
    def restore_checkpoint(self, name: str) -> bool:
        """Restore from checkpoint"""
        checkpoint_dir = self.base_path / ".checkpoints" / name
        
        if not checkpoint_dir.exists():
            print(f"Checkpoint {name} not found")
            return False
        
        try:
            # Read metadata
            with open(checkpoint_dir / "metadata.json", 'r') as f:
                metadata = json.load(f)
            
            # Restore files
            for path in metadata["paths"]:
                src = checkpoint_dir / path
                dest = self.base_path / path
                
                if src.exists():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    
                    if src.is_file():
                        shutil.copy2(src, dest)
                    else:
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(src, dest)
            
            return True
            
        except Exception as e:
            print(f"Error restoring checkpoint {name}: {e}")
            return False