#!/bin/bash
# fix_models.sh - Download correct model files

rm -rf models
mkdir -p models

echo "Downloading correct model files..."

# These are the correct direct download links
pip install gdown

# Age model (Google Drive)
gdown "https://drive.google.com/uc?id=1YCox_4kJ-BYeXq27uUbasu--yz26zUM2" -O models/age_net.caffemodel

# Gender model (Google Drive) 
gdown "https://drive.google.com/uc?id=1wG2a5fq1C90eRkO7vChGaapDzGpMQlm4" -O models/gender_net.caffemodel

# Prototxt files from GitHub
wget -O models/age_deploy.prototxt "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy_age.prototxt"
wget -O models/gender_deploy.prototxt "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy_gender.prototxt"

echo ""
echo "Checking downloaded files..."
ls -lh models/
