from typing import List
import os

# Try to import sentence transformers, but don't fail if not available
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("⚠️ sentence-transformers not available (production mode)")

class EmbeddingsService:
    """
    Embeddings service with fallback for production
    - Local development: Uses sentence-transformers
    - Production (Render): Returns dummy embeddings
    """
    
    def __init__(self):
        self.is_production = os.getenv("ENVIRONMENT") == "production"
        
        if self.is_production or not EMBEDDINGS_AVAILABLE:
            print("📦 Running in production mode (no local embeddings)")
            self.model = None
        else:
            print("📦 Loading embeddings model (one-time download ~100MB)...")
            # all-MiniLM-L6-v2: 384 dimensions, fast, good quality
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
        # Production mode: return dummy embedding
        if self.model is None:
            return [0.0] * 384
        
        # Development mode: use real embeddings
        text = text.strip()
        if not text:
            return [0.0] * 384
        
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
        # Production mode: return dummy embeddings
        if self.model is None:
            return [[0.0] * 384 for _ in texts]
        
        # Development mode: use real embeddings
        texts = [t.strip() if t else "" for t in texts]
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
        # Production mode: return 0
        if self.model is None or not EMBEDDINGS_AVAILABLE:
            return 0.0
        
        # Development mode: calculate real similarity
        a = np.array(embedding1)
        b = np.array(embedding2)
        
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
    
    if service.model is None:
        print("⚠️ Running in production mode - embeddings are disabled")
        print("Set ENVIRONMENT=development to test with real embeddings")
    else:
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