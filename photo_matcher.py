#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
iCloud Photo Face Matching Script
---------------------------------
This script processes a directory of photos or a single photo file from an iCloud backup,
analyzes photos for specific faces based on reference image(s), and copies matching photos
to designated subdirectories based on matching results.
"""

import argparse
import face_recognition
import logging
import os
import shutil
import time
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union


# Configure main logging to only log to file (not console)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("photo_match_log.txt")
    ]
)
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Process photos to find those with matching faces'
    )
    
    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--input-dir',
        help='Path to a directory of photos'
    )
    input_group.add_argument(
        '--input-file',
        help='Path to a single photo file'
    )
    
    # Reference options (mutually exclusive)
    reference_group = parser.add_mutually_exclusive_group(required=True)
    reference_group.add_argument(
        '--reference',
        help='Path to a single reference face image'
    )
    reference_group.add_argument(
        '--reference-dir',
        help='Path to a directory of reference face images'
    )
    
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.8,
        help='Matching confidence threshold (0.0-1.0, default: 0.8)'
    )
    
    parser.add_argument(
        '--output',
        default='./matched_photos',
        help='Output directory for matched photos (default: ./matched_photos)'
    )
    
    args = parser.parse_args()
    
    # Validate threshold value
    if not 0.0 <= args.threshold <= 1.0:
        parser.error("Threshold must be between 0.0 and 1.0")
    
    return args


def validate_paths(args: argparse.Namespace) -> Tuple[
    Union[Path, None], Union[Path, None], Union[Path, None], Union[Path, None], Path, Path, Path, Path, logging.Logger, float, float
]:
    """
    Validate all input paths from command line arguments.
    
    Returns:
        Tuple containing validated paths for:
        - input_dir: Path to directory of photos (or None)
        - input_file: Path to single photo file (or None)
        - reference_image: Path to single reference image (or None)
        - reference_dir: Path to directory of reference images (or None)
        - output_dir: Path to output directory
        - matched_dir: Path to matched photos subdirectory
        - almost_matched_dir: Path to almost matched photos subdirectory
        - not_matched_dir: Path to not matched photos subdirectory
        - run_logger: Logger specific to this run
        - threshold: User-defined confidence threshold
        - almost_threshold: Threshold for almost matched (0.1 below threshold)
    """
    # Validate input path (directory or file)
    input_dir = None
    input_file = None
    
    if args.input_dir:
        input_dir = Path(args.input_dir)
        if not input_dir.exists() or not input_dir.is_dir():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
        # Check if directory contains at least one valid image
        valid_images = [f for f in input_dir.iterdir() 
                        if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png')]
        if not valid_images:
            raise ValueError(f"No valid JPEG/PNG images found in input directory: {input_dir}")
    
    if args.input_file:
        input_file = Path(args.input_file)
        if not input_file.exists() or not input_file.is_file():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        if input_file.suffix.lower() not in ('.jpg', '.jpeg', '.png'):
            raise ValueError(f"Input file must be JPEG or PNG: {input_file}")
    
    # Validate reference image/directory
    reference_image = None
    reference_dir = None
    
    if args.reference:
        reference_image = Path(args.reference)
        if not reference_image.exists() or not reference_image.is_file():
            raise FileNotFoundError(f"Reference image not found: {reference_image}")
        if reference_image.suffix.lower() not in ('.jpg', '.jpeg', '.png'):
            raise ValueError(f"Reference image must be JPEG or PNG: {reference_image}")
    
    if args.reference_dir:
        reference_dir = Path(args.reference_dir)
        if not reference_dir.exists() or not reference_dir.is_dir():
            raise FileNotFoundError(f"Reference directory not found: {reference_dir}")
        
        # Check if directory contains at least one valid image
        valid_images = [f for f in reference_dir.iterdir() 
                        if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png')]
        if not valid_images:
            raise ValueError(f"No valid JPEG/PNG images found in reference directory: {reference_dir}")
    
    # Get thresholds
    threshold = args.threshold
    almost_threshold = max(0.0, threshold - 0.1)  # 0.1 below threshold, but not below 0.0
    
    # Create output directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_output_dir = Path(args.output)
    output_dir = base_output_dir.parent / f"{base_output_dir.name}_{timestamp}"
    
    # Remove output directory if it exists (fresh start)
    if output_dir.exists():
        logger.info(f"Removing existing output directory: {output_dir}")
        shutil.rmtree(output_dir)
    
    # Create output directory and subdirectories
    output_dir.mkdir(parents=True, exist_ok=True)
    matched_dir = output_dir / "matched"
    matched_dir.mkdir(exist_ok=True)
    almost_matched_dir = output_dir / "almost_matched"
    almost_matched_dir.mkdir(exist_ok=True)
    not_matched_dir = output_dir / "not_matched"
    not_matched_dir.mkdir(exist_ok=True)
    
    # Create run-specific log file in the output directory
    log_file_path = output_dir / "log.txt"
    
    # Create a logger for this specific run - file only, no console output
    run_logger = logging.getLogger(f"run_{timestamp}")
    run_logger.setLevel(logging.INFO)
    
    # Add file handler for run-specific log file
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', '%Y-%m-%d %H:%M:%S'))
    run_logger.addHandler(file_handler)
    
    # Make sure the run logger doesn't propagate to the root logger to avoid duplicate logs
    run_logger.propagate = False
    
    # Create detailed threshold information
    threshold_ranges = (
        f"Confidence threshold ranges:\n"
        f"  MATCHED:       >= {threshold:.2f}\n"
        f"  ALMOST MATCHED: {almost_threshold:.2f} to {threshold-0.01:.2f}\n"
        f"  NOT MATCHED:    < {almost_threshold:.2f}"
    )
    
    # Log initial setup information
    logger.info(f"Created output directory with timestamp: {output_dir}")
    logger.info(f"Run-specific log file created at: {log_file_path}")
    logger.info(threshold_ranges)
    
    run_logger.info(f"Created output directory with timestamp: {output_dir}")
    run_logger.info(f"Run-specific log file created at: {log_file_path}")
    run_logger.info(threshold_ranges)
    
    # Print initial information to console (not through logger)
    print(f"\nOutput directory: {output_dir}")
    print(f"Log file: {log_file_path}")
    print(f"\n{threshold_ranges}\n")
    print(f"Starting processing...")
    
    return (input_dir, input_file, reference_image, reference_dir, output_dir, 
            matched_dir, almost_matched_dir, not_matched_dir, run_logger, threshold, almost_threshold)


def get_input_image_paths(
    input_dir: Optional[Path], 
    input_file: Optional[Path],
    run_logger: logging.Logger
) -> List[Path]:
    """
    Get list of image paths from input directory or single file.
    
    Args:
        input_dir: Path to directory of photos (or None)
        input_file: Path to single photo file (or None)
        run_logger: Logger specific to this run
        
    Returns:
        List of paths to images to be processed
    """
    image_paths = []
    
    if input_dir:
        # Get all valid image files from directory
        for file_path in input_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in ('.jpg', '.jpeg', '.png'):
                image_paths.append(file_path)
        
        # Sort paths for consistent processing order
        image_paths.sort()
        logger.info(f"Found {len(image_paths)} images in directory: {input_dir}")
        run_logger.info(f"Found {len(image_paths)} images in directory: {input_dir}")
    
    elif input_file:
        # Single file mode
        image_paths = [input_file]
        logger.info(f"Processing single image file: {input_file}")
        run_logger.info(f"Processing single image file: {input_file}")
    
    return image_paths


def load_reference_encodings(
    reference_image: Optional[Path], 
    reference_dir: Optional[Path],
    run_logger: logging.Logger
) -> Dict[str, List]:
    """
    Load face encodings from reference image(s).
    
    Args:
        reference_image: Path to single reference image (or None)
        reference_dir: Path to directory of reference images (or None)
        run_logger: Logger specific to this run
        
    Returns:
        Dictionary mapping reference image filenames to face encodings
    """
    reference_encodings = {}
    
    if reference_image:
        # Process single reference image
        try:
            image = face_recognition.load_image_file(reference_image)
            face_locations = face_recognition.face_locations(image)
            
            if not face_locations:
                raise ValueError(f"No faces detected in reference image: {reference_image}")
            
            if len(face_locations) > 1:
                warning_msg = f"Multiple faces detected in reference image: {reference_image}. Using the first face."
                logger.warning(warning_msg)
                run_logger.warning(warning_msg)
            
            face_encodings = face_recognition.face_encodings(image, face_locations)
            reference_encodings[reference_image.name] = face_encodings[0]
            
            log_msg = f"Loaded reference face from: {reference_image}"
            logger.info(log_msg)
            run_logger.info(log_msg)
            
        except Exception as e:
            error_msg = f"Error processing reference image {reference_image}: {e}"
            logger.error(error_msg)
            run_logger.error(error_msg)
            raise
    
    elif reference_dir:
        # Process directory of reference images
        processed = 0
        skipped = 0
        max_reference_images = 100  # Limit as per requirement
        
        for img_path in reference_dir.glob('*'):
            if processed >= max_reference_images:
                warning_msg = f"Reached limit of {max_reference_images} reference images. Skipping remaining images."
                logger.warning(warning_msg)
                run_logger.warning(warning_msg)
                break
                
            if img_path.is_file() and img_path.suffix.lower() in ('.jpg', '.jpeg', '.png'):
                try:
                    image = face_recognition.load_image_file(img_path)
                    face_locations = face_recognition.face_locations(image)
                    
                    if not face_locations:
                        warning_msg = f"No faces detected in reference image: {img_path}. Skipping."
                        logger.warning(warning_msg)
                        run_logger.warning(warning_msg)
                        skipped += 1
                        continue
                    
                    if len(face_locations) > 1:
                        warning_msg = f"Multiple faces detected in reference image: {img_path}. Using the first face."
                        logger.warning(warning_msg)
                        run_logger.warning(warning_msg)
                    
                    face_encodings = face_recognition.face_encodings(image, face_locations)
                    reference_encodings[img_path.name] = face_encodings[0]
                    processed += 1
                    
                except Exception as e:
                    error_msg = f"Error processing reference image {img_path}: {e}"
                    logger.error(error_msg)
                    run_logger.error(error_msg)
                    skipped += 1
        
        if not reference_encodings:
            raise ValueError("No valid reference faces found in the reference directory")
        
        log_msg = f"Loaded {processed} reference faces, skipped {skipped} invalid images"
        logger.info(log_msg)
        run_logger.info(log_msg)
    
    return reference_encodings


def update_progress(processed: int, total: int, status: str = ""):
    """
    Display progress bar with percentage and status.
    
    Args:
        processed: Number of items processed
        total: Total number of items
        status: Additional status information
    """
    percentage = int((processed / total) * 100) if total > 0 else 0
    bar_length = 30
    filled_length = int(bar_length * processed // total) if total > 0 else 0
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    progress_text = f"\rProgress: {percentage}% |{bar}| {processed}/{total} images processed {status}"
    sys.stdout.write(progress_text)
    sys.stdout.flush()


def process_images(
    image_paths: List[Path],
    reference_encodings: Dict[str, List],
    threshold: float,
    almost_threshold: float,
    output_dir: Path,
    matched_dir: Path,
    almost_matched_dir: Path,
    not_matched_dir: Path,
    run_logger: logging.Logger,
    batch_size: int = 20
) -> Tuple[int, int, int, int, int]:
    """
    Process images to find faces matching the reference encodings.
    
    Args:
        image_paths: List of paths to images to process
        reference_encodings: Dictionary of reference face encodings
        threshold: Matching confidence threshold
        almost_threshold: Threshold for almost matched (0.1 below threshold)
        output_dir: Path to output directory
        matched_dir: Path to matched photos subdirectory
        almost_matched_dir: Path to almost matched photos subdirectory
        not_matched_dir: Path to not matched photos subdirectory
        run_logger: Logger specific to this run
        batch_size: Number of images to process in each batch
        
    Returns:
        Tuple containing counts of (processed, matched, almost_matched, not_matched, error) images
    """
    processed_count = 0
    matched_count = 0
    almost_matched_count = 0
    not_matched_count = 0
    error_count = 0
    total_images = len(image_paths)
    
    # Convert reference encodings to list for face_recognition library
    reference_names = list(reference_encodings.keys())
    reference_encodings_list = [reference_encodings[name] for name in reference_names]
    
    # Process images in batches to manage memory usage
    for i in range(0, total_images, batch_size):
        batch = image_paths[i:i+batch_size]
        
        for img_path in batch:
            try:
                # Show progress
                processed_count += 1
                update_progress(processed_count, total_images)
                
                # Load and process image
                image = face_recognition.load_image_file(img_path)
                face_locations = face_recognition.face_locations(image)
                
                if not face_locations:
                    # Copy to not_matched directory
                    shutil.copy2(img_path, not_matched_dir)
                    
                    # Log unmatched photo (no faces)
                    log_msg = (
                        f"Not matched: {img_path.name} - No faces detected\n"
                        f"Moved to {not_matched_dir}"
                    )
                    logger.info(log_msg)
                    run_logger.info(log_msg)
                    
                    not_matched_count += 1
                    continue
                
                # Extract face encodings
                face_encodings = face_recognition.face_encodings(image, face_locations)
                
                # Compare with reference encodings
                match_found = False
                almost_match_found = False
                matching_references = []
                almost_matching_references = []
                best_confidences = []
                highest_confidence = 0.0
                
                for face_encoding in face_encodings:
                    # Get distances (lower distance = better match)
                    face_distances = face_recognition.face_distance(reference_encodings_list, face_encoding)
                    
                    # Convert distances to confidences (1.0 - distance)
                    face_confidences = [(reference_names[j], 1.0 - dist) for j, dist in enumerate(face_distances)]
                    face_confidences.sort(key=lambda x: x[1], reverse=True)
                    
                    # Record top 5 confidences for this face
                    if face_confidences:
                        best_confidences.append((f"Face #{len(best_confidences)+1}", face_confidences[:5]))
                        
                        # Check if this face's highest confidence is greater than our current highest
                        if face_confidences[0][1] > highest_confidence:
                            highest_confidence = face_confidences[0][1]
                    
                    # Check for matches above threshold
                    for ref_name, confidence in face_confidences:
                        if confidence >= threshold:
                            matching_references.append((ref_name, confidence))
                            match_found = True
                        elif confidence >= almost_threshold:
                            almost_matching_references.append((ref_name, confidence))
                            almost_match_found = True
                
                # Categorize based on highest match
                if match_found:
                    # Sort matching references by confidence (highest first)
                    matching_references.sort(key=lambda x: x[1], reverse=True)
                    best_match = matching_references[0]
                    
                    # Copy matched image to matched subdirectory
                    shutil.copy2(img_path, matched_dir)
                    
                    # Format match details with line breaks and indentation
                    match_details = "\n    " + "\n    ".join([f"{ref} ({conf:.2f})" for ref, conf in matching_references])
                    
                    # Log the match details
                    log_msg = (
                        f"Matched: {img_path.name} with {len(face_locations)} face(s), "
                        f"confidence {best_match[1]:.2f} against:{match_details}\n"
                        f"Moved to {matched_dir}"
                    )
                    logger.info(log_msg)
                    run_logger.info(log_msg)
                    
                    matched_count += 1
                    
                elif almost_match_found:
                    # Sort almost matching references by confidence (highest first)
                    almost_matching_references.sort(key=lambda x: x[1], reverse=True)
                    best_almost_match = almost_matching_references[0]
                    
                    # Copy to almost_matched directory
                    shutil.copy2(img_path, almost_matched_dir)
                    
                    # Format best confidence details for logging
                    confidence_details = ""
                    for face_name, confidences in best_confidences:
                        confidence_details += f"\n    {face_name} best scores:"
                        for ref, conf in confidences:
                            confidence_details += f"\n        {ref} ({conf:.2f})"
                    
                    # Format almost match details with line breaks and indentation
                    almost_match_details = "\n    " + "\n    ".join([f"{ref} ({conf:.2f})" for ref, conf in almost_matching_references])
                    
                    # Log almost matched photo
                    log_msg = (
                        f"Almost matched: {img_path.name} with {len(face_locations)} face(s) - "
                        f"Best match score {best_almost_match[1]:.2f} (threshold {threshold}, almost range {almost_threshold:.2f}-{threshold-0.01:.2f})."
                        f"\nAlmost matches:{almost_match_details}"
                        f"{confidence_details}\n"
                        f"Moved to {almost_matched_dir}"
                    )
                    logger.info(log_msg)
                    run_logger.info(log_msg)
                    
                    almost_matched_count += 1
                    
                else:
                    # Copy to not_matched directory
                    shutil.copy2(img_path, not_matched_dir)
                    
                    # Format best confidence details for logging
                    confidence_details = ""
                    for face_name, confidences in best_confidences:
                        confidence_details += f"\n    {face_name} best scores:"
                        for ref, conf in confidences:
                            confidence_details += f"\n        {ref} ({conf:.2f})"
                    
                    # Log unmatched photo (no matches above threshold or in almost range)
                    log_msg = (
                        f"Not matched: {img_path.name} with {len(face_locations)} face(s) - "
                        f"No matches above threshold {threshold} or in almost range {almost_threshold:.2f}-{threshold-0.01:.2f}."
                        f"{confidence_details}\n"
                        f"Moved to {not_matched_dir}"
                    )
                    logger.info(log_msg)
                    run_logger.info(log_msg)
                    
                    not_matched_count += 1
                
            except Exception as e:
                error_msg = f"Error processing image {img_path}: {e}"
                logger.error(error_msg)
                run_logger.error(error_msg)
                error_count += 1
                update_progress(processed_count, total_images, f"(Error: {e})")
    
    # Final progress update
    update_progress(processed_count, total_images, "- Completed!")
    print()  # New line after progress updates
    
    return processed_count, matched_count, almost_matched_count, not_matched_count, error_count


def main():
    """Main function to run the iCloud photo face matching script."""
    try:
        start_time = datetime.now()
        logger.info("Starting iCloud photo face matching process")
        
        # Parse command line arguments
        args = parse_arguments()
        
        # Validate paths
        (input_dir, input_file, reference_image, reference_dir, output_dir, matched_dir, 
         almost_matched_dir, not_matched_dir, run_logger, threshold, almost_threshold) = validate_paths(args)
        
        # Get list of image paths to process
        image_paths = get_input_image_paths(input_dir, input_file, run_logger)
        
        # Load reference face encodings
        reference_encodings = load_reference_encodings(reference_image, reference_dir, run_logger)
        
        # Process images to find matches
        processed_count, matched_count, almost_matched_count, not_matched_count, error_count = process_images(
            image_paths, reference_encodings, threshold, almost_threshold, output_dir, 
            matched_dir, almost_matched_dir, not_matched_dir, run_logger
        )
        
        # Log summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        summary_msg = (
            f"Processing complete: {processed_count} images processed, "
            f"{matched_count} matches found, {almost_matched_count} almost matches, "
            f"{not_matched_count} not matched, {error_count} errors. "
            f"Duration: {duration:.2f} seconds"
        )
        logger.info(summary_msg)
        run_logger.info(summary_msg)
        
        # Display summary
        print("\nSummary:")
        print(f"  Images processed: {processed_count}")
        print(f"  Matches found: {matched_count} (saved to {matched_dir})")
        print(f"  Almost matches: {almost_matched_count} (saved to {almost_matched_dir})")
        print(f"  Not matched: {not_matched_count} (saved to {not_matched_dir})")
        print(f"  Errors encountered: {error_count}")
        print(f"  Results saved to: {output_dir}")
        print(f"  Run log file: {output_dir}/log.txt")
        print(f"  Main log file: photo_match_log.txt")
        print(f"  Duration: {duration:.2f} seconds")
        
        # Performance stats
        if duration > 0 and processed_count > 0:
            rate = processed_count / duration
            print(f"  Processing rate: {rate:.2f} images per second")
        
    except Exception as e:
        error_msg = f"An error occurred: {e}"
        logger.error(error_msg)
        print(f"\nError: {error_msg}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 