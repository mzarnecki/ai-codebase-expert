import unittest

from app.db.parser.PHPParser import PHPParser

class PHPParserTest(unittest.TestCase):
    def test_PHPParser_returnsCorrectData_whenPHPCodeGiven(self):
        php_code = """<?php
            declare(strict_types=1);
            
            namespace service;
            
            use League\Pipeline\StageInterface;
            use service\pipeline\Payload;
            
            final class DocumentProvider extends AbstractDocumentRepository implements StageInterface
            {
                public function getQueryForL2Distance(int $limit = 10): string
                {
                    return "SELECT name, text from document order by embedding <-> :embeddingPrompt limit {$limit};";
                }
            
                public function getQueryForCosineDistance(int $limit = 10): string
                {
                    return "SELECT name, text from document order by 1 - (embedding <=> :embeddingPrompt) limit {$limit};";
                }
            }"""
        expected = {
            'class_name': 'DocumentProvider',
            'dependencies': ['Pipeline/StageInterface', 'pipeline/Payload'],
            'methods': ['getQueryForL2Distance', 'getQueryForCosineDistance'],
            'parent_class': 'AbstractDocumentRepository'
        }
        parsed = PHPParser().parse_code(php_code)
        self.assertEqual(expected, parsed)

    def test_PHPParser_returnsEmptyDictValues_whenNoPHPCodeGiven(self):
        php_code = "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum"
        expected = {
            "class_name": None,
            "parent_class": None,
            "methods": None,
            "dependencies": [],
        }
        parsed = PHPParser().parse_code(php_code)
        self.assertEqual(expected, parsed)