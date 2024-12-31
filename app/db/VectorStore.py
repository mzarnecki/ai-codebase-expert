from langchain_postgres import PGVector
from app import utils

class VectorStore:
    def get_vector_store(collection_name: str)->PGVector:
        connection = "postgresql+psycopg://project_solver:project_solver@localhost:6024/project_solver"
        embedding_model = utils.configure_embedding_model()

        vector_db = PGVector(
            embeddings=embedding_model,
            collection_name=collection_name,
            connection=connection,
            use_jsonb=True,
        )
        return vector_db