from core.simulation import Optimizer
import json

def test_diversity():
    print("Testing Optimizer Diversity...")
    # Mock data or use real if possible, but localized to speed up
    results = Optimizer.run_optimization_api(index_choice="EGX30")
    
    if not results:
        print("No results found.")
        return

    print(f"Found {len(results)} results.")
    
    # Check for identical scores
    scores = [r['score'] for r in results]
    unique_scores = set(scores)
    
    print(f"Unique Scores: {len(unique_scores)} / {len(results)}")
    
    if len(unique_scores) < 2:
        print("WARNING: Identical results detected!")
    else:
        print("SUCCESS: Diverse results generated.")

if __name__ == "__main__":
    test_diversity()
