import cv2
import numpy as np

default_blank = np.zeros((500, 500, 3), dtype=np.uint8)

def get_corners(location_data, size_of_cortical, target_size):
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')

    # Calculate min and max coordinates
    for key in location_data.keys():
        x, y = key[0], key[1]
        if x < min_x:
            min_x = x
        if x > max_x:
            max_x = x
        if y < min_y:
            min_y = y
        if y > max_y:
            max_y = y

    # Normalize coordinates based on size_of_cortical
    normalized_min_x = min_x / (size_of_cortical[0] - 1)
    normalized_max_x = max_x / (size_of_cortical[0] - 1)
    normalized_min_y = min_y / (size_of_cortical[1] - 1)
    normalized_max_y = max_y / (size_of_cortical[1] - 1)

    # Flip the y-coordinates
    flipped_min_y = 1 - normalized_max_y
    flipped_max_y = 1 - normalized_min_y

    # Convert normalized coordinates to target size
    top_left = (int(normalized_min_x * target_size[0]), int(flipped_min_y * target_size[1]))
    bottom_right = (int(normalized_max_x * target_size[0]), int(flipped_max_y * target_size[1]))

    return top_left, bottom_right


# example location_data: {'0-0-0': 100, '0-1-0': 100 . . .}, example size_of_cortical: [32, 16, 1]
def process_image(image, location_data=None, size_of_cortical=None):
    copied_image = image.copy()

    # Resize the image while maintaining aspect ratio
    target_width = 400
    original_height, original_width = copied_image.shape[:2]
    aspect_ratio = original_width / original_height
    target_height = int(target_width / aspect_ratio)
    resized_frame = cv2.resize(copied_image, (target_width, target_height))

    if location_data and size_of_cortical:
        top_left, bottom_right = get_corners(location_data, size_of_cortical, (target_width, target_height))

        # Define the border thickness
        border_thickness = 3

        # Draw the outer black rectangle (border)
        cv2.rectangle(resized_frame,
                      (top_left[0] - border_thickness, top_left[1] - border_thickness),
                      (bottom_right[0] + border_thickness, bottom_right[1] + border_thickness),
                      (0, 0, 0), border_thickness)

        # Draw the inner green rectangle
        cv2.rectangle(resized_frame, top_left, bottom_right, (0, 255, 0), 2)
        return resized_frame
    return resized_frame

def blank_image(location_data=None):
    global default_blank
    resized_frame = default_blank

    if location_data:
        top_left, bottom_right = get_corners(location_data, size_of_cortical=default_blank.shape[1::-1], target_size=resized_frame.shape[1::-1])

        # Define the border thickness
        border_thickness = 3

        # Draw the outer black rectangle (border)
        cv2.rectangle(resized_frame,
                      (top_left[0] - border_thickness, top_left[1] - border_thickness),
                      (bottom_right[0] + border_thickness, bottom_right[1] + border_thickness),
                      (0, 0, 0), border_thickness)

        # Draw the inner green rectangle
        cv2.rectangle(resized_frame, top_left, bottom_right, (0, 255, 0), 2)

        return resized_frame
    return default_blank
