# check_models.py
import os
import hashlib

models_dir = "models"
files = [
    "age_deploy.prototxt",
    "age_net.caffemodel",
    "gender_deploy.prototxt", 
    "gender_net.caffemodel"
]

print("=" * 50)
print("CHECKING MODEL FILES")
print("=" * 50)

for f in files:
    path = os.path.join(models_dir, f)
    if os.path.exists(path):
        size = os.path.getsize(path)
        with open(path, 'rb') as file:
            content = file.read()
            md5 = hashlib.md5(content).hexdigest()
        
        # Check if it's actually a valid file or HTML error page
        if content.startswith(b'<!DOCTYPE') or content.startswith(b'<html'):
            print(f"❌ {f}: {size} bytes - THIS IS AN HTML ERROR PAGE!")
        elif f.endswith('.caffemodel') and size < 10000:
            print(f"❌ {f}: {size} bytes - TOO SMALL for a model!")
        elif f.endswith('.prototxt') and size < 100:
            print(f"❌ {f}: {size} bytes - TOO SMALL!")
        else:
            print(f"✅ {f}: {size} bytes - MD5: {md5[:16]}...")
    else:
        print(f"❌ {f}: NOT FOUND")

# Expected sizes:
# age_deploy.prototxt: ~2,300 bytes
# age_net.caffemodel: ~41,000,000 bytes (41MB)
# gender_deploy.prototxt: ~2,300 bytes  
# gender_net.caffemodel: ~41,000,000 bytes (41MB)
