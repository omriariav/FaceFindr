Product Requirements Document (PRD) for iCloud Photo Face Matching Script
1. Overview
This PRD outlines the requirements for a Python script to process a directory of photos or a single photo file extracted from an iCloud backup, analyze the photos, identify those containing specific faces based on a user-provided reference image or a directory of reference images, and move matching photos to a designated directory. The script will help users save relevant photos and free up iPhone storage by organizing and filtering media.
2. Objectives

Enable users to process a directory of photos or a single photo file from an iCloud backup.
Implement facial recognition to match photos containing user-defined faces.
Allow users to provide either a single reference image or a directory of reference images for face matching.
Allow users to configure a matching confidence threshold for face recognition.
Move matched photos to a specified directory for organization.
Optimize iPhone storage by identifying and retaining only relevant photos.

3. Scope
The script will:

Accept a directory containing photos (JPEG/PNG) or a single photo file from an iCloud backup.
Process images to detect faces.
Compare detected faces against a single reference face image or multiple reference images in a directory.
Move images meeting a user-defined matching threshold to a specified output directory.
Provide a command-line interface (CLI) for user inputs and configuration.

The script will not:

Modify original photos or metadata.
Support video or non-image media files.
Access iCloud directly (requires manual extraction of photos).
Provide a graphical user interface (GUI).

4. User Stories

As a user, I want to provide a directory of photos or a single photo file from an iCloud backup so that the script can process them.
As a user, I want to specify a single reference face image or a directory of reference images so that the script can identify photos containing those faces.
As a user, I want to set a matching confidence threshold so that I can control the accuracy of face matches.
As a user, I want matched photos to be moved to a new directory so that I can easily access and save relevant photos.
As a user, I want the script to log its actions so that I can verify which photos were processed and moved.

5. Functional Requirements
5.1 Input Handling

Photo Input:
Accept either:
A directory containing photo files (JPEG/PNG) extracted from an iCloud backup.
A single photo file (JPEG/PNG).


Validate that the input directory exists and contains at least one valid image file, or that the single photo file is valid.
Support common image formats (JPEG, PNG).


Reference Face Input:
Accept either:
A single reference image file (JPEG/PNG) containing the target face.
A directory containing multiple reference images (JPEG/PNG) of one or more target faces.


Validate that each reference image contains exactly one detectable face.
If a reference directory is provided, process all valid images (JPEG/PNG) in the directory and extract facial encodings from each.


User Configuration:
Accept a matching confidence threshold (e.g., 0.0 to 1.0, default 0.8) via CLI argument.
Accept an output directory path for matched photos (default: ./matched_photos).
Accept either a --reference argument (for a single image) or a --reference-dir argument (for a directory of images).
Accept either a --input-dir argument (for a directory of photos) or a --input-file argument (for a single photo).



5.2 Image Processing

Face Detection:
Use a facial recognition library (e.g., face_recognition or OpenCV) to detect faces in each input image.
Skip images with no detectable faces.


Face Matching:
Extract facial encodings from the reference image(s):
For a single reference image, use its facial encoding.
For a reference directory, aggregate facial encodings from all valid images.


Compare encodings of detected faces in input photos against the reference encoding(s), using the user-defined confidence threshold.
Consider a match if any reference encoding meets the threshold.


File Handling:
Copy matched photos to the specified output directory, preserving original filenames.
Ensure original photos remain unchanged in the source directory or file location.
Create the output directory if it does not exist.



5.3 Logging and Output

Log all actions (e.g., files processed, faces detected, matches found, files moved) to a text file (e.g., photo_match_log.txt).
Include details of which reference image(s) contributed to each match when using a reference directory.
Display a summary of results in the CLI (e.g., total photos processed, matches found, errors encountered).
Handle errors gracefully (e.g., corrupted images, missing files, invalid reference images) and log them without crashing.

6. Non-Functional Requirements

Performance:
Process at least 100 photos per minute on a standard consumer laptop (e.g., 2.5 GHz CPU, 8 GB RAM).
Optimize for memory usage to handle large photo directories (e.g., thousands of images) and reference directories with up to 100 images.


Reliability:
Handle edge cases (e.g., missing files, invalid images, multiple faces in reference images, empty input or reference directory) without crashing.
Ensure no data loss or corruption of original files.


Security:
Do not store or transmit user images or data outside the local machine.
Use only trusted, open-source libraries for facial recognition.


Compatibility:
Support Python 3.8+.
Run on macOS, Windows, and Linux.
Support common image formats (JPEG, PNG).



7. Technical Specifications

Programming Language: Python 3.8+
Libraries:
face_recognition (for face detection and matching) or OpenCV with dlib.
argparse for CLI argument parsing.
shutil for file operations.
logging for logging actions.
os and pathlib for file system operations.


CLI Interface:python photo_matcher.py [--input-dir <photo_dir> | --input-file <photo_file>] [--reference <reference_image.jpg> | --reference-dir <reference_dir>] --threshold <0.0-1.0> --output <output_dir>


--input-dir: Path to a directory of photos (mutually exclusive with --input-file).
--input-file: Path to a single photo file (mutually exclusive with --input-dir).
--reference: Path to a single reference face image (mutually exclusive with --reference-dir).
--reference-dir: Path to a directory of reference face images (mutually exclusive with --reference).
--threshold: Matching confidence threshold (default: 0.8).
--output: Output directory for matched photos (default: ./matched_photos).


Error Handling:
Validate input and reference paths and file formats.
Check for single face in each reference image.
Ensure --input-dir or --input-file is provided, but not both.
Ensure --reference or --reference-dir is provided, but not both.
Skip invalid or corrupted images (in input or reference directory) with logged warnings.
Handle empty input or reference directories with a clear error message.


Logging:
Log file format: photo_match_log.txt with timestamped entries.
Example log entry: [YYYY-MM-DD HH:MM:SS] Processed image1.jpg: 1 face detected, matched with confidence 0.85 against reference image ref_image1.jpg, moved to ./matched_photos.



8. Assumptions

Users have manually extracted photos from an iCloud backup into a directory or as a single file.
Images are in standard formats (JPEG, PNG).
Reference images in the directory (if used) contain one face each and are in JPEG/PNG format.
Users have sufficient disk space for the output directory.
The reference image or directory contains clear faces for reliable matching.

9. Risks and Mitigations

Risk: Facial recognition may produce false positives or negatives, especially with multiple reference images.
Mitigation: Allow users to adjust the confidence threshold and review logs for manual verification, including reference image details.


Risk: Large photo directories or reference directories may cause performance issues.
Mitigation: Optimize processing with batch handling, limit reference directory size (e.g., 100 images), and provide progress updates.


Risk: Corrupted or missing photo or reference images may disrupt processing.
Mitigation: Implement robust error handling and skip problematic files.


Risk: Privacy concerns with facial recognition.
Mitigation: Process all data locally, use trusted libraries, and clearly document data handling.



10. Success Metrics

Script successfully processes a directory with 1,000+ photos or a single photo in under 10 minutes.
At least 90% accuracy in face matching (based on user feedback and manual verification), including with multiple reference images.
No crashes or data loss during processing.
Positive user feedback on ease of use and storage optimization.

11. Future Enhancements

Support for video frame extraction and face matching.
Batch processing of multiple reference faces with distinct output directories per face.
GUI for easier configuration and visualization of matches.
Integration with cloud storage (e.g., iCloud, Google Drive) for automatic backup of matched photos.

12. Appendix

Sample Input:
Directory: Contains files like image1.jpg, image2.png, etc.
Single file: A single image like photo.jpg.


Recommended Libraries:
face_recognition: Simple API, built on dlib, suitable for small-scale use.
OpenCV: Faster processing, more customizable, but requires additional setup.



