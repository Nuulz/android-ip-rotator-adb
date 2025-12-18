from PIL import Image
import os

INPUT_PNG = "icon.png"
OUTPUT_ICO = "icon.ico"

sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]

if not os.path.isfile(INPUT_PNG):
    print(f"[ERROR] {INPUT_PNG} not found")
    exit(1)

img = Image.open(INPUT_PNG).convert("RGBA")

img.save(
    OUTPUT_ICO,
    format="ICO",
    sizes=sizes
)

print(f"[OK] ICO generated: {OUTPUT_ICO}")