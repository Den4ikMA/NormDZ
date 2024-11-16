import os
from PIL import Image
import numpy as np

def compress_image_to_text(image_path):
    img = Image.open(image_path).convert('L')  # Convert to grayscale
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
            avg_color = block.mean()  # Average color value in grayscale
            
            # Encode as '1' for black (avg < 128) and '0' for white (avg >= 128)
            symbol = '1' if avg_color < 128 else '0'
            compressed_output += symbol
        compressed_output += '\n'

    return compressed_output

def decompress_text_to_image(compressed_text, output_image_path):
    lines = compressed_text.strip().split('\n')
    
    # Calculate height and width for the reconstructed image
    height = len(lines) * 2
    width = len(lines[0]) * 2

    # Create an empty array for the image data with correct dimensions
    image_data = np.zeros((height, width), dtype=np.uint8)

    for y, line in enumerate(lines):
        for x, char in enumerate(line):
            color_value = 255 if char == '0' else 0  # '0' -> white (255), '1' -> black (0)
            
            # Fill the corresponding 2x2 block with the color value
            image_data[y*2:y*2+2, x*2:x*2+2] = color_value

    # Convert array back to an image and save it
    reconstructed_image = Image.fromarray(image_data)

    # Save directly without resizing to avoid distortion
    reconstructed_image.save(output_image_path)

def text_to_bytes(input_file_path, output_file_path):
    with open(input_file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Split the content into chunks of 8 characters
    byte_chunks = [content[i:i + 8] for i in range(0, len(content), 8)]

    # Convert each chunk to bytes and store in a list
    byte_array = []
    for chunk in byte_chunks:
        # Pad the chunk with spaces if it's less than 8 characters
        if len(chunk) < 8:
            chunk = chunk.ljust(8)  # Pad with spaces to ensure it has 8 characters
        byte_array.append(chunk.encode('utf-8'))  # Convert to bytes

    # Write the byte representation to the output file
    with open(output_file_path, 'wb') as output_file:
        for byte_chunk in byte_array:
            output_file.write(byte_chunk)

def convert_text_to_bytes(input_text_file_path, output_text_file_path):
    with open(input_text_file_path, 'r', encoding='utf-8') as input_file:
        binary_string = input_file.read().replace('\n', '')  # Remove newlines

    # Ensure the binary string length is a multiple of 8
    if len(binary_string) % 8 != 0:
        binary_string = binary_string.ljust(len(binary_string) + (8 - len(binary_string) % 8), '0')

    # Split the binary string into chunks of 8
    byte_chunks = [binary_string[i:i + 8] for i in range(0, len(binary_string), 8)]

    # Write the byte chunks to the output text file
    with open(output_text_file_path, 'w', encoding='utf-8') as output_file:
        for byte in byte_chunks:
            output_file.write(byte + '\n')  # Write each byte on a new line

def convert_grouped_bytes_to_decimal(input_grouped_bytes_file_path, output_decimal_file_path):
    with open(input_grouped_bytes_file_path, 'r', encoding='utf-8') as input_file:
        lines = input_file.readlines()

    decimal_values = []
    
    for line in lines:
        binary_str = line.strip()  # Remove any surrounding whitespace/newlines
        
        if binary_str:   # Check if the line is not empty
            decimal_value = int(binary_str, 2)  # Convert binary string to decimal integer
            decimal_values.append(str(decimal_value))   # Store as a string for writing later
    
    with open(output_decimal_file_path, 'w', encoding='utf-8') as output_file:
        output_file.write('\n'.join(decimal_values))   # Write all decimal values to the file

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
            
            output_bytes_file_path = os.path.join(input_directory, f'{os.path.splitext(filename)[0]}_compressed_bytes.bin')
            text_to_bytes(text_file_path, output_bytes_file_path)
            print(f'Saved byte representation to {output_bytes_file_path}')
            
            output_grouped_text_file_path = os.path.join(input_directory, f'{os.path.splitext(filename)[0]}_grouped_bytes.txt')
            convert_text_to_bytes(text_file_path, output_grouped_text_file_path)
            print(f'Saved grouped bytes representation to {output_grouped_text_file_path}')
            
            # Convert grouped bytes from binary to decimal values
            output_decimal_values_file_path = os.path.join(input_directory, f'{os.path.splitext(filename)[0]}_decimal_values.txt')
            convert_grouped_bytes_to_decimal(output_grouped_text_file_path, output_decimal_values_file_path)
            print(f'Saved decimal values representation to {output_decimal_values_file_path}')
            
            output_image_path = os.path.join(input_directory, f'{os.path.splitext(filename)[0]}_reconstructed.png')
            decompress_text_to_image(compressed_text, output_image_path)
            print(f'Saved reconstructed image to {output_image_path}')

# Example usage
input_directory = r'C:\pics'
process_images_in_directory(input_directory)
