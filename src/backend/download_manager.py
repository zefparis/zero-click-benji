import logging
import shutil
import os
from typing import Dict, Any

class DownloadManager:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def download_project_as_zip(self, project_path: str, output_path: str = "red_sword_project.zip"):
        self.logger.info(f"Downloading project as ZIP from {project_path} to {output_path}")
        try:
            shutil.make_archive(output_path.replace(".zip", ""), 'zip', project_path)
            self.logger.info(f"Project downloaded as ZIP to {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error downloading project as ZIP: {e}")
            return False