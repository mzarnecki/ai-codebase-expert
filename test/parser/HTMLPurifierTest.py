import unittest

from app.db.parser.HTMLPurifier import HTMLPurifier

class HTMLPurifierTest(unittest.TestCase):
    def test_HTMLPurifier_removesHTMLTags(self):
        text_content = 'Some text'
        purified = HTMLPurifier.purify(f'<div>{text_content}</div>')
        self.assertEqual(text_content, purified)