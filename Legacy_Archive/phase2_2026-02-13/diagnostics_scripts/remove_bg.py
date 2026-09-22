from PIL import Image
import collections

def remove_background_flood(input_path, output_path, tolerance=30):
    try:
        print(f"Processing {input_path} with Flood Fill...")
        img = Image.open(input_path).convert("RGBA")
        width, height = img.size
        pixels = img.load()
        
        # Helper to check if pixel is "white-ish" enough to be background
        def is_white(pos):
            r, g, b, a = pixels[pos]
            return r > (255 - tolerance) and g > (255 - tolerance) and b > (255 - tolerance)

        # BFS Queue
        q = collections.deque()
        visited = set()
        
        # Start from corners if they are white
        corners = [(0, 0), (width-1, 0), (0, height-1), (width-1, height-1)]
        for c in corners:
            if is_white(c):
                q.append(c)
                visited.add(c)
        
        # Function to get neighbors
        def get_neighbors(x, y):
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    yield (nx, ny)

        count = 0
        while q:
            curr = q.popleft()
            pixels[curr] = (255, 255, 255, 0) # Make Transparent
            count += 1
            
            for nb in get_neighbors(*curr):
                if nb not in visited:
                    if is_white(nb):
                        visited.add(nb)
                        q.append(nb)
        
        img.save(output_path, "PNG")
        print(f"Done! Removed {count} background pixels. Saved to {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Use higher tolerance for JPEGs
    remove_background_flood("temp_logo.jpg", "Hours.png", tolerance=50)
