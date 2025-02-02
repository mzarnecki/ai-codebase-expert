import os
import re

from app.db.parser.PHPParser import PHPParser

class DocumentMetadataCreator:

    def __init__(self):
        self.php_parser = PHPParser()

    def create_metadata(self, root: str, file: str, text: str)->dict[str, str]:
        file_path = re.sub("\\.\\./data/\\w+/\\w+/", "", os.path.join(root, file))
        metadata = {
            "source": file,
            "file_path": file_path,
        }
        metadata |= self.php_parser.parse_code(text)
        return metadata