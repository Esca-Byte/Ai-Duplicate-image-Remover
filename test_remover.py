import os
import shutil
import unittest
from PIL import Image, ImageDraw
from duplicate_remover import DuplicateRemover

class TestDuplicateRemover(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_images_advanced"
        os.makedirs(self.test_dir, exist_ok=True)
        
        # 1. Base Image (High Qual) - Needs a pattern for pHash
        self.img_base_path = os.path.join(self.test_dir, "base_hq.jpg")
        self.img = Image.new('RGB', (500, 500), color = 'white')
        d = ImageDraw.Draw(self.img)
        d.rectangle([10, 10, 200, 400], fill="red", outline="black")
        d.line((0, 0) + self.img.size, fill=128)
        self.img.save(self.img_base_path, quality=100)
        
        # 2. Resized Version (Low Qual)
        self.img_small_path = os.path.join(self.test_dir, "base_small.jpg")
        img_small = self.img.resize((50, 50))
        img_small.save(self.img_small_path)
        
        # 3. Different Image - Different pattern
        self.img_diff_path = os.path.join(self.test_dir, "diff.jpg")
        img_diff = Image.new('RGB', (500, 500), color = 'blue')
        d2 = ImageDraw.Draw(img_diff)
        d2.ellipse([50, 50, 400, 400], fill="green")
        img_diff.save(self.img_diff_path)
        
    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
    def test_fuzzy_matching_keeps_best(self):
        # We expect the small image to be marked as duplicate of the big one
        remover = DuplicateRemover(self.test_dir, method='phash', threshold=10)
        duplicates = remover.find_duplicates()
        
        self.assertEqual(len(duplicates), 1)
        
        dup_file, orig_file = duplicates[0]
        
        # Verify the "duplicate" (to be removed) is the small one
        self.assertEqual(os.path.abspath(dup_file), os.path.abspath(self.img_small_path))
        # Verify the "original" (to be kept) is the HQ one
        self.assertEqual(os.path.abspath(orig_file), os.path.abspath(self.img_base_path))

    def test_no_false_positives(self):
        remover = DuplicateRemover(self.test_dir, method='phash', threshold=10)
        duplicates = remover.find_duplicates()
        
        # Ensure the blue image is NOT in the duplicates list
        for d, o in duplicates:
            self.assertNotEqual(os.path.abspath(d), os.path.abspath(self.img_diff_path))
            self.assertNotEqual(os.path.abspath(o), os.path.abspath(self.img_diff_path))

if __name__ == '__main__':
    unittest.main()
