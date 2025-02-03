import unittest

from app.db.DocumentMetadataCreator import DocumentMetadataCreator


class DocumentMetadatCreatorTest(unittest.TestCase):
    def test_DocumentMetadatCreator_returnsCorrectMetadata(self):
        root = 'data/code/companyhouseProjectCode/common/components/company/'
        file = 'CourtTownMapper.php'
        metadata = DocumentMetadataCreator().create_metadata(root, file, 'some text blabla bla')
        expected = {
            'class_name': None,
            'dependencies': [],
            'file_path': 'data/code/companyhouseProjectCode/common/components/company/CourtTownMapper.php',
            'methods': None,
            'parent_class': None,
            'source': 'CourtTownMapper.php'
        }
        self.assertEqual(expected, metadata)