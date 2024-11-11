import os
from PIL import Image
import numpy as np

def compress_image_to_text(image_path):
    img = Image.open(image_path).convert('RGB')  # Convert to RGB
    width, height = img.size

    # Ensure dimensions are even for 2x2 blocks
    new_width = (width // 2) * 2
    new_height = (height // 2) * 2
    img = img.resize((new_width, new_height))

    data = np.array(img)
    compressed_output = ""

    # Iterate over the image in blocks of 2x2 pixels
    for y in range(0, new_height, 2):
        for x in range(0, new_width, 2):
            block = data[y:y+2, x:x+2]
            avg_color = block.mean(axis=(0, 1)).astype(int)
            symbol = chr(avg_color[0] // 16 + 32)  # Scale to printable ASCII range
            compressed_output += symbol
        compressed_output += '\n'

    return compressed_output

def decompress_text_to_image(compressed_text, output_image_path):
    lines = compressed_text.strip().split('\n')
    
    # Calculate height and width for the reconstructed image
    height = len(lines) * 2
    width = len(lines[0]) * 2

    # Create an empty array for the image data with correct dimensions
    image_data = np.zeros((height, width, 3), dtype=np.uint8)

    for y, line in enumerate(lines):
        for x, char in enumerate(line):
            avg_color_value = (ord(char) - 32) * 16  # Reverse the scaling
            color = (avg_color_value, avg_color_value, avg_color_value)  # Grayscale color
            
            # Fill the corresponding 2x2 block with the average color
            image_data[y*2:y*2+2, x*2:x*2+2] = color

    # Convert array back to an image and save it
    reconstructed_image = Image.fromarray(image_data)

    # Save directly without resizing to avoid distortion
    reconstructed_image.save(output_image_path)

def process_images_in_directory(input_directory):
    for filename in os.listdir(input_directory):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(input_directory, filename)
            print(f'Processing {image_path}...')
            
            compressed_text = compress_image_to_text(image_path)
            
            text_file_path = os.path.join(input_directory, f'{os.path.splitext(filename)[0]}_compressed.txt')
            with open(text_file_path, 'w', encoding='utf-8') as text_file:
                text_file.write(compressed_text)
            
            print(f'Saved compressed text to {text_file_path}')
            
            output_image_path = os.path.join(input_directory, f'{os.path.splitext(filename)[0]}_reconstructed.png')
            decompress_text_to_image(compressed_text, output_image_path)
            print(f'Saved reconstructed image to {output_image_path}')

# Example usage
input_directory = r'D:\оригинал картинок'
process_images_in_directory(input_directory)
