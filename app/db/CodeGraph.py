import networkx as nx

class CodeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_file(self, path, metadata):
        self.graph.add_node(path, **metadata)

        # Add edges for class inheritance
        if metadata.get('parent_class'):
            self.graph.add_edge(path, metadata['parent_class'])

        # Add edges for dependencies
        for dep in metadata.get('dependencies', []):
            self.graph.add_edge(path, dep)

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