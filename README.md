# 🖼️ Smart Duplicate Image Remover

> **Clean up your photo library with the power of AI.**  
> A blazing fast, intelligent Python tool that finds and removes duplicate images—even if they've been resized, compressed, or slightly edited.

![Python](https://img.shields.io/badge/Python-3.7%2B-blue?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg?style=for-the-badge)

## 🚀 Key Features

*   **🧠 AI-Powered Fuzzy Matching**: Uses **Perceptual Hashing (pHash)** to detect images that look similar, not just identical bytes. Finds resized, compressed, or format-converted duplicates.
*   **⚡ Multi-Core Performance**: optimized with parallel processing (`ProcessPoolExecutor`) to scan thousands of images in seconds.
*   **💎 Smart Retention**: Automatically identifies and **keeps the best version** (highest resolution or largest file size) and discards the lower-quality duplicates.
*   **🛡️ Safety First**: By default, duplicates are moved to a `duplicates_found` folder for review. Permanent deletion is optional.
*   **🎯 Exact Match Mode**: Supports standard MD5 hashing for finding 100% identical files.

---

## 📦 Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/duplicate-image-remover.git
    cd duplicate-image-remover
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

---

## 🛠️ Usage

### 1. Basic Scan (Exact Duplicates)
Finds files that are exactly identical (byte-for-byte). fast and safe.
```bash
python duplicate_remover.py "C:\Path\To\Your\Images"
```

### 2. Smart Scan (Similar Images) ✨ *Recommended*
Finds images that look the same, even if one is a thumbnail or compressed.
```bash
python duplicate_remover.py "C:\Path\To\Your\Images" --method phash
```
*   **Note**: The tool will automatically keep the **Higher Quality** image and move the lower quality one.

### 3. Delete Duplicates
Permanently delete duplicates instead of moving them.
```bash
python duplicate_remover.py "C:\Path\To\Images" --method phash --action delete
```

### Options
| Flag | Description | Default |
|------|-------------|---------|
| `--method` | `md5` (exact) or `phash` (fuzzy/visual) | `md5` |
| `--threshold`| Sensitivity for fuzzy matching (lower = stricter). | `5` |
| `--action` | `move` (safely move) or `delete` (remove). | `move` |
| `--no-recursive` | Do not scan subfolders. | `False` |

---

## 🧪 How It Works

1.  **Scanning**: The script walks through your directory (recursively) and picks up all image files (`.jpg`, `.png`, `.webp`, etc.).
2.  **Hashing**:
    *   **MD5**: distinct digital fingerprint. Changes if even one bit changes.
    *   **pHash**: visual fingerprint. Stays similar even if the image is resized or color-corrected.
3.  **Comparison**:
    *   It groups images with the same (or similar) hash.
    *   It calculates the **Hamming Distance** between hashes to find neighbors.
4.  **Resolution Logic**: When a group of duplicates is found, the script checks the **resolution (width x height)**. The largest image is marked as the "Original" and kept safe.

---

## 🤝 Contributing

Contributions are welcome!
1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Report

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.
