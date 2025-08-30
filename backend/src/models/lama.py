from simple_lama_inpainting import SimpleLama
from PIL import Image

simple_lama = SimpleLama()
    
def inpaint(img_path, mask_path, save_path):
    image = Image.open(img_path).convert("RGB")
    mask = Image.open(mask_path).convert('L')

    result = simple_lama(image, mask)
    result.save(save_path)