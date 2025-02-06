from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import RunnableLambda
from pydantic import Field

class CustomGraphRetriever(BaseRetriever):
    base_retriever: BaseRetriever = Field(...)
    enhancer: RunnableLambda = Field(...)

    def __init__(self, base_retriever, enhancer):
        super().__init__(
            base_retriever=base_retriever,
            enhancer=enhancer
        )

    def _get_relevant_documents(self, query, *, run_manager):
        # Retrieve documents
        docs = self.base_retriever.get_relevant_documents(query)
        print(docs)
        # Enhance documents
        return self.enhancer.invoke(docs)