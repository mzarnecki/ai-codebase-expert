import pickle

import networkx as nx

class CodeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_file(self, metadata):
        self.graph.add_node(metadata['file_path'], **metadata)
        # Add edges for class inheritance
        if metadata.get('parent_class'):
            self.graph.add_edge(metadata['file_path'], metadata['parent_class'])
        # Add edges for dependencies
        for dep in metadata.get('dependencies', []):
            self.graph.add_edge(metadata['file_path'], dep)

    @classmethod
    def load(cls, path):
        instance = cls()
        with open(path, 'rb') as f:
            instance.graph = pickle.load(f)
        return instance

    def get_relations(self, file_path):
        node = self.graph.nodes.get(file_path, {})
        return {
            'parent': node.get('parent_class'),
            'dependencies': node.get('dependencies', []),
            'all_related': list(nx.descendants(self.graph, file_path))
        }


# Usage in retrieval
def enhance_with_relations(retrieved_docs, code_graph):
    enhanced_docs = []
    for doc in retrieved_docs:
        related_nodes = list(nx.descendants(code_graph.graph, doc.metadata['file_path']))
        enhanced_docs.append({
            **doc,
            "related_files": related_nodes
        })
    return enhanced_docs
