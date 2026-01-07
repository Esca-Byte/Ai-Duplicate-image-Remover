import os
import hashlib
import argparse
import shutil
import concurrent.futures
from pathlib import Path
from PIL import Image
import imagehash
from tqdm import tqdm
from collections import defaultdict

# --- Helper Functions (Must be top-level for multiprocessing) ---

def get_image_info(file_path):
    """
    Returns a tuple (file_path, hash object/string, resolution, file_size).
    Returns None if error.
    """
    try:
        # Get File Size
        file_size = os.path.getsize(file_path)
        
        # Open Image to get Resolution and Hash
        with Image.open(file_path) as img:
            resolution = img.size[0] * img.size[1] # Total pixels
            
            # We calculate both slightly differently, but for simplicity:
            # If we are doing phash, we return the imagehash object.
            # If md5, we return string.
            # To keep it generic in this helper, let's just do the calculation based on global or passed arg?
            # Multiprocessing arguments are tricky. Let's return the opened image object? No, can't pickle.
            # We will default to returning specific things.
            
            # Let's calculate pHash always as it's cheap enough usually, 
            # OR we can make this function specialized.
            # To support both efficiently, let's handle MD5 separately if needed.
            # For now, let's just return the PIL image object? No.
            pass
    except Exception:
        return None

def process_file_md5(file_path):
    """Worker function for MD5."""
    try:
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for block in iter(lambda: f.read(65536), b''):
                md5.update(block)
        
        # Get extra info for "Keep Best"
        file_size = os.path.getsize(file_path)
        # For MD5, resolution is less relevant for "exact" dupes, 
        # but if we have collision/same content different metadata, size helps.
        # We'll try to get resolution too if it's an image.
        resolution = 0
        try:
            with Image.open(file_path) as img:
                resolution = img.size[0] * img.size[1]
        except:
            pass
            
        return (file_path, md5.hexdigest(), resolution, file_size)
    except Exception:
        return None

def process_file_phash(file_path):
    """Worker function for pHash."""
    try:
        with Image.open(file_path) as img:
            # Calculate pHash
            img_hash = imagehash.phash(img)
            resolution = img.size[0] * img.size[1]
            file_size = os.path.getsize(file_path)
            return (file_path, img_hash, resolution, file_size)
    except Exception:
        # Corrupt image or not an image
        return None

# --- Main Class ---

class DuplicateRemover:
    def __init__(self, directory, method='md5', threshold=5, recursive=True):
        self.directory = directory
        self.method = method
        self.threshold = threshold # Only for pHash
        self.recursive = recursive
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}

    def scan_files(self):
        """Scans directory and returns list of image paths."""
        files_to_check = []
        if self.recursive:
            for root, _, files in os.walk(self.directory):
                for file in files:
                    if Path(file).suffix.lower() in self.image_extensions:
                        files_to_check.append(os.path.join(root, file))
        else:
            for file in os.listdir(self.directory):
                 if Path(file).suffix.lower() in self.image_extensions:
                    files_to_check.append(os.path.join(self.directory, file))
        return files_to_check

    def find_duplicates(self):
        files = self.scan_files()
        print(f"Scanning {len(files)} images using {self.method}...")
        
        # Choose worker
        worker = process_file_md5 if self.method == 'md5' else process_file_phash
        
        results = []
        # Parallel execution
        with concurrent.futures.ProcessPoolExecutor() as executor:
            # tqdm for progress bar
            results = list(tqdm(executor.map(worker, files), total=len(files), unit="img"))
        
        # Filter out failed reads (None)
        results = [r for r in results if r is not None]
        
        duplicates = [] # List of tuples: (duplicate_file, original_file)
        
        if self.method == 'md5':
            # Exact matching
            seen = {} # hash -> best_file_info
            
            for file_path, file_hash, res, size in results:
                if file_hash in seen:
                    # We found a collision. Now decide which is "Original" (Best)
                    existing_path, existing_res, existing_size = seen[file_hash]
                    
                    # Compare
                    # For MD5, content is identical. 
                    # Prefer larger file size (maybe metadata?) or just first found?
                    # Let's just prefer the one already there, mark current as dup.
                    duplicates.append((file_path, existing_path))
                else:
                    seen[file_hash] = (file_path, res, size)
                    
        elif self.method == 'phash':
            # Fuzzy matching
            # This is O(N^2) effectively if we compare all against all, but we can allow O(N) by grouping?
            # No, for hamming distance with threshold, simple dict doesn't work.
            # We need to compare specific hashes.
            # For speed, we will sort hashes? No, perceptual hashes aren't linear like that.
            # We will simply maintain a list of "Unique" images and compare each new one to them.
            
            unique_images = [] # List of (hash, file_path, resolution, file_size)
            
            print("Comparing images for similarity...")
            # We process sequentially for comparison
            for file_path, file_hash, res, size in results:
                is_duplicate = False
                best_match = None
                
                # Check against all known unique images
                for i, (u_hash, u_path, u_res, u_size) in enumerate(unique_images):
                    if file_hash - u_hash <= self.threshold:
                        # Convert both hashes to str for debug if needed
                        # Found a match!
                        is_duplicate = True
                        
                        # LOGIC: Who is better?
                        # Prefer Higher Resolution
                        if res > u_res:
                            # The new one is better. The old "unique" is actually the duplicate.
                            # We need to move the old unique to duplicates list
                            # and update the unique list with the new one.
                            duplicates.append((u_path, file_path)) # Old is dup of New
                            unique_images[i] = (file_hash, file_path, res, size) # Update "Best"
                        elif res < u_res:
                            # Old is better. New is duplicate.
                            duplicates.append((file_path, u_path))
                        else:
                            # Equal resolution. Prefer larger file size (less compression)
                            if size > u_size:
                                duplicates.append((u_path, file_path))
                                unique_images[i] = (file_hash, file_path, res, size)
                            else:
                                duplicates.append((file_path, u_path))
                        
                        break # Found its group, stop looking
                
                if not is_duplicate:
                    unique_images.append((file_hash, file_path, res, size))
                    
        return duplicates

def main():
    parser = argparse.ArgumentParser(description="Find and remove duplicate images with enhanced features.")
    parser.add_argument("directory", help="Directory to scan")
    parser.add_argument("--method", choices=['md5', 'phash'], default='md5', help="md5 (exact) or phash (fuzzy)")
    parser.add_argument("--threshold", type=int, default=5, help="Similarity threshold for pHash (default: 5). Lower is stricter.")
    parser.add_argument("--action", choices=['move', 'delete'], default='move', help="Action to take on duplicates")
    parser.add_argument("--no-recursive", action="store_true", help="Don't scan subfolders")
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print("Invalid directory.")
        return
        
    remover = DuplicateRemover(args.directory, method=args.method, threshold=args.threshold, recursive=not args.no_recursive)
    duplicates = remover.find_duplicates()
    
    if not duplicates:
        print("No duplicates found.")
        return
        
    print(f"Found {len(duplicates)} duplicates.")
    
    # Process Actions
    if args.action == 'delete':
        print("Deleting duplicates...")
        for dup, orig in duplicates:
            try:
                os.remove(dup)
                print(f"Deleted {os.path.basename(dup)} (Duplicate of {os.path.basename(orig)})")
            except Exception as e:
                print(f"Error deleting {dup}: {e}")
    else:
        dest_dir = os.path.join(args.directory, "duplicates_found")
        os.makedirs(dest_dir, exist_ok=True)
        print(f"Moving duplicates to {dest_dir}...")
        for dup, orig in duplicates:
            try:
                filename = os.path.basename(dup)
                target = os.path.join(dest_dir, filename)
                
                # Handle name collision
                if os.path.exists(target):
                    base, ext = os.path.splitext(filename)
                    c = 1
                    while os.path.exists(os.path.join(dest_dir, f"{base}_{c}{ext}")):
                        c+=1
                    target = os.path.join(dest_dir, f"{base}_{c}{ext}")
                    
                shutil.move(dup, target)
                print(f"Moved {os.path.basename(dup)} -> {os.path.basename(target)} \n   (Duplicate of {os.path.basename(orig)})")
            except Exception as e:
                print(f"Error moving {dup}: {e}")

if __name__ == "__main__":
    main()
