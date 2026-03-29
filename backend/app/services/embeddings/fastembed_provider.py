from fastembed import TextEmbedding

from app.services.embeddings.base import EmbeddingProvider


class FastEmbedProvider(EmbeddingProvider):
    def __init__(self, model_name: str, batch_size: int = 64) -> None:
        self._model_name = model_name
        self._batch_size = batch_size
        self._model = TextEmbedding(model_name=model_name)
        probe = list(self._model.embed(["dimension probe"], batch_size=1))
        self._dimension = len(probe[0]) if probe else 0

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = list(self._model.embed(texts, batch_size=self._batch_size))
        return [vector.tolist() for vector in vectors]
