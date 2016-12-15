# glitch art generator written in python by steephen salmon
# script will read all images from an input directory and generate glicth art based on them

import os
from PIL import Image, ImageDraw, ImageOps, ImageChops
import argparse
from random import randint, random, sample
from itertools import cycle
import binascii
OUTPUT_FORMAT = ".png"
IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.tif', '.bmp', 'gif', 'tiff']


def save_image(image, prefix):
    random_hash = str(binascii.b2a_hex(os.urandom(15)))[2:-1]
    output_image_name = prefix + "_" + random_hash + "_" + OUTPUT_FORMAT
    output_dir = "/home/stephen.salmon/Pictures/ggen/one"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # output_dir_path = os.path.join(script_dir, output_dir)
    output_dir_path = os.path.join(script_dir, output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    image_path = os.path.join(output_dir, output_image_name)
    print("Image saved to {0}".format(image_path))
    image.save(image_path)


def load_images(input_dir):
    images = []
    for file in os.listdir(input_dir):
        filepath = os.path.join(input_dir, file)
        if os.path.isfile(filepath):
            if os.path.splitext(filepath)[1].lower() in IMAGE_FORMATS:
                img = Image.open(filepath)
                images.append(img)
    return images


def resize_images(images, size="fixed"):
    '''Resize all images to the max or min dimensions of the images'''
    fixed = (800, 800)
    size_dict = {'max': max, 'min': min}
    if size == "fixed":
        dims = fixed
    else:
        dims = list(map(size_dict[size], zip(*[y.size for y in images])))
    resized_images = [image.resize(dims, Image.ANTIALIAS) for image in images]
    return resized_images


def get_average_color(image, color_size=2048):
    colors = image.getcolors(color_size * 4)
    max_oc, most_pres = 0, 0
    try:
        for c in colors:
            if c[0] > max_oc:
                (max_oc, most_pres) = c
        return most_pres
    except TypeError:
        raise Exception("too many colors in the image")


def sections(width, height, n):
    for x in range(0, width, n):
        for y in range(0, height, n):
            if (x + n > width) or (y + n > height):
                continue
            yield (x, y, x+n, y+n)


def create_block_mask(image, threshold=500, block_size=10):
    w, h = image.size
    block_mask_image = Image.new('RGB', (w, h), color='black')
    block_draw = ImageDraw.Draw(block_mask_image, 'RGB')
    for section in sections(w, h, block_size):
        im = image.crop(section)
        if sum(get_average_color(im)) < threshold:
            block_draw.rectangle(section, (255, 255, 255))
        else:
            pass
    block_mask_image = block_mask_image.convert("L")
    return block_mask_image


def pixelate(input_image, pixelsize=20):
    w,h = input_image.size
    input_image = input_image.resize((int(input_image.size[0] / pixelsize),
                                int(input_image.size[1] / pixelsize)), Image.NEAREST)
    image = input_image.resize((int(input_image.size[0] * pixelsize),
                                int(input_image.size[1] * pixelsize)), Image.NEAREST)
    image = image.resize((w,h),3)
    return image


def random_pixel_mask(input_image, flip=True, threshold=400, blockmax=50):
    w, h = input_image.size
    rand_pix_size = randint(2, randint(10,blockmax))
    rand_block_size = randint(5, randint(10,blockmax))
    pixelated_img = pixelate(input_image, pixelsize=rand_pix_size)
    pix_block_mask = create_block_mask(pixelated_img, threshold=threshold, block_size=rand_block_size)
    if flip:
        pix_block_mask = ImageOps.mirror(pix_block_mask)
    pix_block_mask = pix_block_mask.resize((w, h), 3)
    pix_block_mask = pix_block_mask.convert("L")
    return pix_block_mask


def random_channel_merge(images):
    channels = []
    if len(images) < 3:
        print("Error: Need at least three input images in the directory")
        exit(2)
    for image in sample(images, 3):
        for channel in image.split():
            channels.append(channel)
    three_channels = (sample(channels, 3))
    output_image = Image.merge('RGB', three_channels)
    return output_image


def combine_images_with_mask(image1, image2, pixelmask):
    return Image.composite(image1, image2, pixelmask)


def twin_random_channel_pixel_masking(input_images, threshold=400):
    image1 = random_channel_merge(input_images)
    image2 = random_channel_merge(input_images)
    random_pix_mask = random_pixel_mask(image1, threshold=threshold)
    output_image = combine_images_with_mask(image1, image2, random_pix_mask)
    return output_image


def something_without_channels(input_images, threshold=400):
    frandimage = input_images[randint(0,len(input_images)-1)]
    random_pix_mask = random_pixel_mask(frandimage, threshold=threshold)
    output_image = combine_images_with_mask(frandimage, frandimage, random_pix_mask)
    return output_image


def offset_image(image, offset=100):
    return ImageChops.offset(image, offset)


def self_glitch(image, offset=100, threshold=200):
    offset = offset_image(image, offset=offset)
    mask = random_pixel_mask(image, threshold=threshold)
    output_image = combine_images_with_mask(offset, image, mask)
    return output_image

def get_horizontal_stripes(width, height, n):
    """Yield a list of size n of horizontal stripe coordinates
    for the image"""
    for x in range(0, int(height), int(int(height) / int(n))):
        yield (0, x, width, int(x + height / n))


def splice_and_offset(image, no_of_splices=100, offset=100, scaling=2):
    w,h = image.size
    output_image = Image.new('RGB', (w, h))
    #create an offset wave from offset * scaling
    offset_wave = [0, 100, 200, 300, 200, 100]
    cycle_wave = cycle(offset_wave)
    for stripe_coord in get_horizontal_stripes(w, h, no_of_splices):
        slice = image.crop(stripe_coord)
        offset_slice = offset_image(slice, next(cycle_wave))
        output_image.paste(offset_slice, stripe_coord)
    return output_image




def glitch_art_generator(images, threshold=400):
    images[0] = splice_and_offset(images[0], no_of_splices=randint(10,100))
    #images[2] = splice_and_offset(images[2], no_of_splices=100)
    # something_without_channels
    # image1 = twin_random_channel_pixel_masking(images, threshold=threshold)
    #image2 = twin_random_channel_pixel_masking(images, threshold=(threshold/2))
    image1 = something_without_channels(images, threshold=threshold)
    image2 = something_without_channels(images, threshold=(threshold*2))
    image1 = self_glitch(image1, offset=100, threshold=400)
    image1 = image1.transpose(Image.FLIP_LEFT_RIGHT)
    #image1 = splice_and_offset(image1, no_of_splices=10)

    random_pix_mask = random_pixel_mask(images[0], threshold=(threshold))

    output_image = combine_images_with_mask(image1, image2, random_pix_mask)
    # op = self_glitch(output_image, offset=100, threshold=400)
    # op = splice_and_offset(output_image, no_of_splices=10)
    return output_image


def main():
    input_images = load_images(INPUT_DIR)
    input_images = resize_images(input_images, size=SIZE)
    for x in range(0,NUM_IMAGES):
        output = glitch_art_generator(input_images, threshold=randint(100,THRESH_VAL))
        if SHOW_IMAGE:
            output.show()
        save_image(output, "g_art_gen")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Glitch Art Generator')
    parser.add_argument("-n", "--numimages", dest="NUM_IMAGES", default=10, type=int, help="Number of Output Images")
    parser.add_argument("-s", "--show_image", dest="SHOW_IMAGE", action='store_true', default=True, help="Display Images on Creation")
    parser.add_argument("-t", "--threshold", dest="THRESH_VAL", default=400, type=int, help="Threshold Value")
    parser.add_argument("-sz", "--size", dest="SIZE", default='max', choices=['max','min','fixed'], help="Output Image dimensions")
    parser.add_argument("-i", "--input", dest="INPUT_DIR",
                        default="/home/stephen.salmon/Pictures/test_input/three", help="Image Input Directory")
    #add output directory
    #more options
    try:
        args = parser.parse_args()
    except:
        print("Args Error")
        parser.print_help()
        exit(2)

    THRESH_VAL = args.THRESH_VAL
    INPUT_DIR = args.INPUT_DIR
    SHOW_IMAGE = args.SHOW_IMAGE
    NUM_IMAGES = args.NUM_IMAGES
    SIZE = args.SIZE
    main()

