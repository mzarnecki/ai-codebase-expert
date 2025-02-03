import unittest

from app.db.CodeGraph import CodeGraph

class HTMLCodeGraphTest(unittest.TestCase):
    def test_codeGraph_returnsCorrectDependencies(self):
        graph = CodeGraph()
        file_path = 'service/DocumentProvider'
        metadata = {
            'file_path': file_path,
            'class_name': 'DocumentProvider',
            'dependencies': ['Pipeline/StageInterface', 'pipeline/Payload'],
            'methods': ['getQueryForL2Distance', 'getQueryForCosineDistance'],
            'parent_class': 'AbstractDocumentRepository'
        }
        graph.add_file(metadata=metadata)
        other_metadata = {
            'file_path': 'service/OtherDocumentProvider',
            'class_name': 'OtherDocumentProvider',
            'dependencies': ['OtherPipeline/StageInterface', 'pipeline/OtherPayload'],
            'methods': ['getOtherQueryForL2Distance', 'getOtherQueryForCosineDistance'],
            'parent_class': 'OtherAbstractDocumentRepository'
        }
        graph.add_file(metadata=other_metadata)
        relations = graph.get_relations(file_path=file_path)

        expected = {
            'parent': 'AbstractDocumentRepository',
            'dependencies': ['Pipeline/StageInterface', 'pipeline/Payload'],
            'methods': ['getQueryForL2Distance', 'getQueryForCosineDistance'],
            'all_related': ['AbstractDocumentRepository',
                'Pipeline/StageInterface',
                'getQueryForCosineDistance',
                'getQueryForL2Distance',
                'pipeline/Payload']
        }

        self.assertEqual(expected, relations)