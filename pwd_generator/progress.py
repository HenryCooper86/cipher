import sys
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ProgressBar:
    def __init__(self, total: int, description: str = "Progress", width: int = 40):
        self.total = total
        self.current = 0
        self.description = description
        self.width = width
        self._enabled = sys.stdout.isatty()
    
    def update(self, n: int = 1):
        self.current = min(self.current + n, self.total)
        if self._enabled:
            self._display()
    
    def _display(self):
        if self.total == 0:
            percent = 100
        else:
            percent = int(100 * self.current / self.total)
        
        filled = int(self.width * self.current / self.total) if self.total > 0 else self.width
        bar = '=' * filled + '-' * (self.width - filled)
        
        sys.stdout.write(f'\r{self.description}: [{bar}] {percent}% ({self.current}/{self.total})')
        sys.stdout.flush()
    
    def finish(self):
        if self._enabled:
            self.current = self.total
            self._display()
            sys.stdout.write('\n')
            sys.stdout.flush()
        else:
            print(f"{self.description}: Complete ({self.total}/{self.total})")


def show_progress(iterable, description: str = "Processing", total: Optional[int] = None):
    if total is None:
        try:
            total = len(iterable)
        except TypeError:
            total = None
    
    if total is None:
        for item in iterable:
            yield item
    else:
        bar = ProgressBar(total, description)
        for item in iterable:
            yield item
            bar.update(1)
        bar.finish()
