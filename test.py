img,_,_ = pcv.readimage(img_path)
p1 = pcv.rgb2gray_lab(img, 'a')
p = cv2.addWeighted(p1, 0.08001, np.zeros(p1.shape, p1.dtype), 100, 245)
p = pcv.closing(p)
p = pcv.closing(cv2.bitwise_not(pcv.threshold.otsu(p)))
p = pcv.closing(p,kernel=pcv.get_kernel(size=(4,4), shape='cross'))



image = cv2.imread(img_path)
hh, ww = image.shape[:2]
maxdim = max(hh, ww)

# illumination normalize
ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)

# separate channels
y, cr, cb = cv2.split(ycrcb)

# get background which paper says (gaussian blur using standard deviation 5 pixel for 300x300 size image)
# account for size of input vs 300
sigma = int(5 * maxdim / 300)
print('sigma: ',sigma)
gaussian = cv2.GaussianBlur(y, (0, 0), sigma, sigma)

# subtract background from Y channel
y = (y - gaussian + 100)

# merge channels back
ycrcb = cv2.merge([y, cr, cb])

#convert to BGR
img = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)

# Image Processing - example operations
a_gray = pcv.rgb2gray_lab(rgb_img=img, channel='a')
bin_mask = pcv.threshold.otsu(gray_img=a_gray, object_type='dark')
clean_mask = pcv.closing(gray_img=bin_mask)
