import time
from data_engine.local_feed_selector import compare_local_sources

print("First call (should take a while)...")
t0 = time.time()
r1 = compare_local_sources()
print(f"Time 1: {time.time() - t0:.2f}s")
print("Recommended:", r1.get('recommended_provider'))

print("Second call (should be instant)...")
t1 = time.time()
r2 = compare_local_sources()
print(f"Time 2: {time.time() - t1:.2f}s")
print("Recommended:", r2.get('recommended_provider'))

print("Third call force_refresh (should take a while)...")
t2 = time.time()
r3 = compare_local_sources(force_refresh=True)
print(f"Time 3: {time.time() - t2:.2f}s")
print("Recommended:", r3.get('recommended_provider'))
