import os
import re

from app.db.parser.HTMLPurifier import HTMLPurifier

class FileContentProvider:

    def get_content(self, root: str, file: str, only_php: bool)->str|None:
        with open(os.path.join(root, file), 'rb') as f:
            if only_php and not file.endswith(".php"):
                return None
            if file.endswith(".png") or file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".mp4"):
                return None
            try:
                text = f.read().decode(errors='replace')
                if file.endswith(".html"):
                    text = HTMLPurifier.purify(text)
                text = re.sub(r'\{[\w_-]+\}', '', text) #remove curly braces as they are interpreted as template params
                return text
            except Exception as e:
                print(e)