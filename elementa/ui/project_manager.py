from typing import List
from PyQt6.QtCore import QSettings

class ProjectManager:
    def __init__(self, qsettings: QSettings, max_items: int = 10):
        self.s = qsettings
        self.max_items = max_items

    def add_recent(self, path: str):
        paths = self.recent_projects()
        if path in paths:
            paths.remove(path)
        paths.insert(0, path)
        self.s.setValue("recent_projects", paths[:self.max_items])

    def recent_projects(self) -> List[str]:
        return self.s.value("recent_projects", [], type=list)
