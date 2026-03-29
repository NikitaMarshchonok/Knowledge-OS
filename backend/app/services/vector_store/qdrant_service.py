from uuid import UUID

from qdrant_client import QdrantClient, models

from app.core.config import get_settings


class QdrantIndexService:
    def __init__(self, vector_size: int) -> None:
        settings = get_settings()
        self.collection_name = settings.qdrant_collection_name
        self.vector_size = vector_size
        self.client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)

    def ensure_collection(self) -> None:
        collections = self.client.get_collections().collections
        names = {collection.name for collection in collections}
        if self.collection_name in names:
            info = self.client.get_collection(self.collection_name)
            size = info.config.params.vectors.size
            if size != self.vector_size:
                raise ValueError(
                    f"Qdrant collection '{self.collection_name}' has vector size {size}, expected {self.vector_size}"
                )
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(size=self.vector_size, distance=models.Distance.COSINE),
        )

    def delete_document_vectors(self, document_id: UUID) -> None:
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=str(document_id)),
                        )
                    ]
                )
            ),
            wait=True,
        )

    def upsert_chunk_vectors(self, points: list[models.PointStruct]) -> None:
        if not points:
            return
        self.client.upsert(collection_name=self.collection_name, points=points, wait=True)
