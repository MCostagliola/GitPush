import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from plantcv import plantcv as pcv

def normalize_intensity(img_data):
    """
    Normalize the intensity of the image to the range 0-255.
    """
    # Convert to float to avoid overflow or underflow losses.
    img_data = img_data.astype(float)
    
    # Calculate the minimum and maximum values
    min_val = img_data.min()
    max_val = img_data.max()
    print(f"Original min: {min_val}, max: {max_val}")
    
    # Normalize the image data to the range 0-1
    img_data_normalized = (img_data - min_val) / (max_val - min_val)
    
    # Scale to the range 0-255
    img_data_normalized = (img_data_normalized * 255).astype(np.uint8)
    
    print(f"Normalized min: {img_data_normalized.min()}, max: {img_data_normalized.max()}")
    
    return img_data_normalized

def show_img(img_path, colormap=None):
    # Load image using Pillow
    img = Image.open(img_path).convert('L')
    img_data = np.array(img)
    
    # Normalize the image intensity
    img_data_normalized = normalize_intensity(img_data)
    
    # Plot the original and normalized images
    plt.figure(figsize=(12, 12))
    
    plt.subplot(2, 2, 1)
    plt.title('Original Image')
    plt.imshow(img_data, cmap=colormap)
    plt.axis('off')
    
    plt.subplot(2, 2, 2)
    plt.title('Normalized Image')
    plt.imshow(img_data_normalized, cmap=colormap)
    plt.axis('off')
    
    plt.subplot(3,2,3)
    plt.title('Original Bin')
    plt.imshow(pcv.closing(pcv.threshold.otsu(img_data)), cmap=colormap)
    plt.axis('off')

    plt.subplot(3,2,4)
    plt.title('Normalized Bin')
    plt.imshow(pcv.closing(pcv.threshold.otsu(img_data_normalized)), cmap=colormap)
    plt.axis('off')

    img,_,_ = pcv.readimage(img_path)

    plt.subplot(3,2,5)
    plt.title('PCV Image')
    plt.imshow(pcv.rgb2gray_lab(img, 'a'), cmap=colormap)
    plt.axis('off')

    plt.subplot(3,2,6)
    plt.title('PCV Bin')
    plt.imshow(pcv.closing(pcv.threshold.otsu(pcv.rgb2gray_lab(img, 'a'))), cmap=colormap)
    plt.axis('off')

    plt.show()
    return img_data, img_data_normalized
    

# Path to your PNG image
#show_img(r"C:\smart\0input_image.png", 'gray')

import cv2
import numpy as np

origm = r"C:\MLearning\training\val_masks\04-07-2024_03-58-Rep404.jpg"
origi = r"C:\MLearning\training\val_images\04-07-2024_03-58-Rep404.jpg"

# read input
image = cv2.imread(origi)
hh, ww = image.shape[:2]
#print(hh, ww)
max = max(hh, ww)

# illumination normalize
ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)

# separate channels
y, cr, cb = cv2.split(ycrcb)

# get background which paper says (gaussian blur using standard deviation 5 pixel for 300x300 size image)
# account for size of input vs 300
sigma = int(5 * max / 300)
#print('sigma: ',sigma)
gaussian = cv2.GaussianBlur(y, (0, 0), sigma, sigma)

# subtract background from Y channel
y = (y - gaussian + 100)

# merge channels back
ycrcb = cv2.merge([y, cr, cb])

#convert to BGR
output = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)

# save results
#cv2.imwrite('retina2_proc.jpg', output)

# show results
cv2.imshow("output", output)
#cv2.waitKey(0)

#g = pcv.rgb2gray_lab(output, 'a')
#bt = pcv.threshold.otsu(g)
#b = pcv.closing(pcv.closing(bt))

#a = cv2.bitwise_not(b)

#img,_,_ = pcv.readimage(origi)
p1 = pcv.rgb2gray_lab(output, 'a')
p = cv2.addWeighted(p1, 0.08001, np.zeros(p1.shape, p1.dtype), 100, 245)
cv2.imshow('2', pcv.opening(cv2.bitwise_not(pcv.threshold.otsu(p))))
p = pcv.opening(p)
p = pcv.closing(cv2.bitwise_not(pcv.threshold.otsu(p)))

#cv2.imshow('a', cv2.imread(origm))
#cv2.imshow('b', a)
cv2.imshow('c', pcv.opening(p,kernel=pcv.get_kernel(size=(4,4), shape='cross')))
cv2.waitKey(0)

'''plt.figure(figsize=(8, 6))
plt.subplot(2, 2, 1)
plt.title('Original Img')
plt.imshow(cv2.imread(origi))
plt.axis('off')

plt.subplot(2, 2, 2)
plt.title('Original Img Norm')
plt.imshow(output)
plt.axis('off')

plt.subplot(2, 2, 3)
plt.title('Original Bin')
plt.imshow(cv2.imread(origm))
plt.axis('off')

plt.subplot(2, 2, 4)
plt.title('Norm Bin')
plt.imshow(a, cmap='gray')
plt.axis('off')

plt.show()'''