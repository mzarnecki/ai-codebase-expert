from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda
from networkx.exception import NetworkXError

from app.db.CodeGraph import CodeGraph
from app.db.EnumDocsCollection import EnumDocsCollection
from app.db.VectorStore import VectorStore
from app.llm.retriever.CustomGraphRetriever import CustomGraphRetriever

class RetrieverFactory:
    def __init__(self):
        self.code_graph = CodeGraph.load('data/graph/graph.pickle')  # Load pre-built graph

    def get_retrievers(self):
        vectordb_code = VectorStore.get_vector_store(EnumDocsCollection.CODE.value)

        base_retriever = vectordb_code.as_retriever(
            search_type='similarity',
            search_kwargs={'k': 8},
            return_source_documents=True,
        )

        # Create graph-aware retriever
        graph_retriever = CustomGraphRetriever(
            base_retriever=base_retriever,
            enhancer=RunnableLambda(self._enhance_documents),  # Wrap with RunnableLambda
        )

        # Documentation retriever
        vectordb_docs = VectorStore.get_vector_store(EnumDocsCollection.DOCUMENTATION.value)
        retriever_docs = vectordb_docs.as_retriever(
            search_type='mmr',
            search_kwargs={'k': 8, "lambda_mult": 0.5},
            return_source_documents=True,
        )

        return graph_retriever, retriever_docs

    def _enhance_documents(self, docs):
        enhanced = []
        emptyRelations = {
            'parent': None,
            'dependencies': [],
            'all_related': []
        }
        for doc in docs:
            metadata = doc.metadata
            if self.code_graph is None:
                relations = emptyRelations.copy()
            else:
                try:
                    relations = self.code_graph.get_relations(metadata['file_path'])
                except NetworkXError:
                    relations = emptyRelations.copy()

            # Create enhanced metadata
            enhanced_metadata = {
                **metadata,
                'parent_file': relations['parent'],
                'dependency_files': relations['dependencies'],
                'all_related_files': relations['all_related']
            }

            # Create new document with expanded content
            enhanced_content = (
                f"File: {metadata['file_path']}\n"
                f"Parent: {relations['parent'] or 'None'}\n"
                f"Dependencies: {', '.join(relations['dependencies']) or 'None'}\n"
                f"Content:\n{doc.page_content}"
            )

            enhanced.append(Document(
                page_content=enhanced_content,
                metadata=enhanced_metadata
            ))
            return enhanced