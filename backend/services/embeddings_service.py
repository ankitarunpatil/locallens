from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np

class EmbeddingsService:
    """
    FREE local embeddings using sentence-transformers
    No API costs, runs on your machine
    """
    
    def __init__(self):
        print("📦 Loading embeddings model (one-time download ~100MB)...")
        
        # all-MiniLM-L6-v2: 384 dimensions, fast, good quality
        # First run downloads the model, then it's cached
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        print("✅ Embeddings model loaded and ready!")
    
    def create_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text
        
        Args:
            text: Input text to embed
            
        Returns:
            List of 384 floats representing the text
        """
        # Clean text
        text = text.strip()
        if not text:
            # Return zero vector for empty text
            return [0.0] * 384
        
        # Generate embedding
        embedding = self.model.encode(text, convert_to_numpy=True)
        
        return embedding.tolist()
    
    def create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts at once (faster)
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        # Clean texts
        texts = [t.strip() if t else "" for t in texts]
        
        # Batch encoding is much faster than one-by-one
        embeddings = self.model.encode(
            texts, 
            convert_to_numpy=True,
            show_progress_bar=True
        )
        
        return embeddings.tolist()
    
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score from -1 to 1 (1 = identical)
        """
        a = np.array(embedding1)
        b = np.array(embedding2)
        
        # Cosine similarity
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)


# Test the service if run directly
if __name__ == "__main__":
    print("Testing EmbeddingsService...\n")
    
    service = EmbeddingsService()
    
    # Test 1: Single embedding
    print("Test 1: Single embedding")
    text = "coffee shop in downtown"
    embedding = service.create_embedding(text)
    print(f"Text: '{text}'")
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}\n")
    
    # Test 2: Batch embeddings
    print("Test 2: Batch embeddings")
    texts = [
        "Italian restaurant with outdoor seating",
        "Cozy cafe with wifi",
        "Park with playground for kids"
    ]
    embeddings = service.create_embeddings_batch(texts)
    print(f"Generated {len(embeddings)} embeddings\n")
    
    # Test 3: Similarity
    print("Test 3: Similarity")
    emb1 = service.create_embedding("coffee shop")
    emb2 = service.create_embedding("cafe with coffee")
    emb3 = service.create_embedding("italian restaurant")
    
    sim_12 = service.similarity(emb1, emb2)
    sim_13 = service.similarity(emb1, emb3)
    
    print(f"'coffee shop' vs 'cafe with coffee': {sim_12:.3f}")
    print(f"'coffee shop' vs 'italian restaurant': {sim_13:.3f}")
    print(f"\n✅ Higher similarity means more related!")