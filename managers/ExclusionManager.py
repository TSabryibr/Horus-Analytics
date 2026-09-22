import os
import json
import logging

logger = logging.getLogger("ExclusionManager")

class ExclusionManager:
    """
    Manages exclusion lists, merging hardcoded sets with dynamic JSON configuration.
    """
    def __init__(self, hardcoded_exclusions, file_path):
        self.hardcoded = set(hardcoded_exclusions)
        self.file_path = file_path
        self._cached_all = None
        self._cached_mtime = None
        
    def get_all(self):
        """Returns union of hardcoded and dynamic exclusions."""
        exclusions = set(self.hardcoded)
        if os.path.exists(self.file_path):
            try:
                current_mtime = os.path.getmtime(self.file_path)
            except OSError:
                current_mtime = None

            if self._cached_all is not None and self._cached_mtime == current_mtime:
                return set(self._cached_all)

            try:
                with open(self.file_path, 'r') as f:
                    dynamic = json.load(f)
                    exclusions.update(dynamic)
                    self._cached_all = set(exclusions)
                    self._cached_mtime = current_mtime
            except Exception as e:
                logger.error(f"CRITICAL: Failed to load exclusions from {self.file_path}: {e}")
        else:
            self._cached_all = set(exclusions)
            self._cached_mtime = None
        return exclusions
        
    def save_dynamic(self, tickers):
        """Helper to save dynamic list to file."""
        try:
            dir_path = os.path.dirname(self.file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
                
            with open(self.file_path, 'w') as f:
                json.dump(list(tickers), f, indent=2)
            try:
                self._cached_mtime = os.path.getmtime(self.file_path)
            except OSError:
                self._cached_mtime = None
            self._cached_all = set(self.hardcoded).union(tickers)
            return True
        except Exception as e:
            print(f"Error saving exclusions: {e}")
            self._cached_all = None
            self._cached_mtime = None
            return False
            
    def add(self, ticker):
        """Adds a ticker to the dynamic exclusion list."""
        current = self.get_all()
        if ticker in current:
            return True # Already excluded (either hardcoded or dynamic)
            
        # Load strictly dynamic part to append
        dynamic = []
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    dynamic = json.load(f)
            except: pass
            
        if ticker not in dynamic:
            dynamic.append(ticker)
            return self.save_dynamic(dynamic)
        return True
        
    def remove(self, ticker):
        """Removes a ticker from the dynamic exclusion list."""
        if ticker in self.hardcoded:
            print(f"Cannot remove {ticker}: It is hardcoded.")
            return False
            
        dynamic = []
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    dynamic = json.load(f)
            except: pass
            
        if ticker in dynamic:
            dynamic.remove(ticker)
            return self.save_dynamic(dynamic)
        return True
