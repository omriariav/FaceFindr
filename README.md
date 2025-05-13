# FaceFindr: Intelligent Photo Face Matching Tool

FaceFindr is a powerful Python tool that uses facial recognition to automatically identify and organize photos containing specific faces. Originally designed for processing iCloud photo libraries, this tool can work with any collection of photos to help you quickly find pictures of specific people.

## 🌊 Motivation

This project was born out of a personal challenge - sorting through a massive 6GB collection of photos from my daughter's kindergarten WhatsApp group. Manually finding pictures of just my daughter among hundreds of class photos was incredibly time-consuming, which inspired the creation of FaceFindr as an automated solution.

## 🌟 Features

- **Flexible Input Options**:
  - Process an entire directory of photos or a single photo file
  - Use a single reference face image or multiple reference images

- **Smart Categorization**:
  - **Matched**: Photos with faces matching above your specified threshold
  - **Almost Matched**: Photos with faces matching just below the threshold (within 0.1)
  - **Not Matched**: Photos with no faces or matches below the "almost" range

- **User-Friendly Experience**:
  - Real-time progress bar with percentage completion
  - Timestamped output directories for each run
  - Detailed logging with match confidence scores
  - Performance statistics upon completion

- **Robust Implementation**:
  - Batch processing to optimize memory usage
  - Comprehensive error handling
  - Configurable matching threshold

## 📋 Requirements

- Python 3.8+
- Required libraries (install via `pip install -r requirements.txt`):
  - face_recognition==1.3.0
  - dlib>=19.20.0
  - numpy>=1.19.0
  - Pillow>=8.0.0

**Note**: The `dlib` library requires additional system dependencies. See the [dlib installation guide](https://github.com/davisking/dlib#installation) for platform-specific instructions.

## 🚀 Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/facefindr.git
   cd facefindr
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 💻 Usage

### Basic Command Format

```bash
python photo_matcher.py --input-dir <photos_directory> --reference <reference_image.jpg> [OPTIONS]
```

### Command-line Arguments

| Argument | Description |
|----------|-------------|
| `--input-dir` | Path to a directory of photos (mutually exclusive with `--input-file`) |
| `--input-file` | Path to a single photo file (mutually exclusive with `--input-dir`) |
| `--reference` | Path to a single reference face image (mutually exclusive with `--reference-dir`) |
| `--reference-dir` | Path to a directory of reference face images (mutually exclusive with `--reference`) |
| `--threshold` | Matching confidence threshold (0.0-1.0, default: 0.8) |
| `--output` | Base name for output directory (default: ./matched_photos) |

### Examples

**Process a directory with a single reference image:**
```bash
python photo_matcher.py --input-dir ./vacation_photos --reference person.jpg --output ./vacation_matches
```

**Process a single photo with a reference image:**
```bash
python photo_matcher.py --input-file family_photo.jpg --reference mom.jpg
```

**Process photos with multiple reference images:**
```bash
python photo_matcher.py --input-dir ./photo_library --reference-dir ./family_faces --threshold 0.7
```

**Use a stricter matching threshold:**
```bash
python photo_matcher.py --input-dir ./photos --reference person.jpg --threshold 0.9
```

## 📁 Output Structure

The script creates a timestamped output directory and organizes photos as follows:

```
matched_photos_YYYYMMDD_HHMMSS/
├── matched/           # Photos with face matches above threshold
├── almost_matched/    # Photos with face matches within 0.1 below threshold
├── not_matched/       # Photos with no matches or below almost-matched range
└── log.txt            # Detailed log of the processing run
```

### Understanding Match Categories

- **Matched**: Confidence score ≥ threshold
- **Almost Matched**: Confidence score between (threshold - 0.1) and (threshold - 0.01)
- **Not Matched**: Confidence score < (threshold - 0.1) or no faces detected

Example with threshold = 0.8:
- Matched: ≥ 0.80
- Almost Matched: 0.70 - 0.79
- Not Matched: < 0.70

## 🔍 How It Works

1. **Reference Loading**: The script loads and encodes facial features from your reference image(s)
2. **Photo Processing**: Each photo is analyzed to detect faces
3. **Face Comparison**: Detected faces are compared against reference face(s) using facial recognition
4. **Categorization**: Photos are copied to appropriate subdirectories based on match confidence
5. **Logging**: Detailed match information is recorded in log files

## ⚙️ Performance Considerations

- **Batch Processing**: Images are processed in batches to manage memory usage
- **Reference Limit**: Reference directory is limited to 100 images maximum
- **Progress Tracking**: Real-time progress bar provides continuous feedback
- **Efficiency**: Photos with no faces are quickly categorized as "not matched"

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📧 Contact

If you have any questions or suggestions, please open an issue on GitHub. 
You can also send me an email - omri.ariav at gmail dot com

---

**FaceFindr** - Find the faces that matter in your photo collection. 