import numpy as np
import time
import cv2 as cv
from pathlib import Path
import random as rd


MIN_MATCH_COUNT=5
FLANN_INDEX_LSH = 6
index_params= dict(algorithm = FLANN_INDEX_LSH,
                   table_number = 6, # 12
                   key_size = 12,     # 20
                   multi_probe_level = 1) #2

f_detector = cv.ORB_create(nfeatures=15000)
#f_matcher = cv.BFMatcher(cv.NORM_HAMMING)
f_matcher = cv.FlannBasedMatcher(index_params)

pattern_path = 'patterns'
patterns = {}
p = Path(pattern_path)
for f in p.iterdir():
    print('read pattern {} '.format(f))
    img = cv.imread(str(f),0)
    img_kp, img_des = f_detector.detectAndCompute(img,None)
    patterns[f.stem] = (img,img_kp,img_des)


def findinscreen(screen,pattern_name,ratio=0.75):
    if not patterns[pattern_name]:
        return None
    st = time.time() * 1000
    ed = 0
    img,img_kp,img_desc = patterns[pattern_name]
    k,screen_desc = f_detector.detectAndCompute(screen,None)
    matches = f_matcher.knnMatch(img_desc,screen_desc,k=2)
# store all the good matches as per Lowe's ratio test.
    good = []
    for m,n in [mm for mm in matches if len(mm) == 2]:
        if m.distance < ratio*n.distance:
            good.append(m)
    try:
        if len(good)>MIN_MATCH_COUNT:
    #        cv.imwrite('{}.png'.format(rd.randint(0,1000)),screen)
            src_pts = np.float32([ img_kp[m.queryIdx].pt for m in good ]).reshape(-1,1,2)
            dst_pts = np.float32([ k[m.trainIdx].pt for m in good ]).reshape(-1,1,2)
            M, mask = cv.findHomography(src_pts, dst_pts, cv.RANSAC,5.0)
            matchesMask = mask.ravel().tolist()
            h,w = img.shape
            pts = np.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2)
            dst = cv.perspectiveTransform(pts,M)
            #print('find img in {} ms'.format(int(time.time() * 1000 - st)))
            return dst
    except:
        pass
    #print('find {} in {} ms'.format(pattern_name,int(time.time() * 1000 - st)))
    return None

def resize(image, width = None, height = None, inter = cv.INTER_AREA):
	dim = None
	(h, w) = image.shape[:2]
	if width is None and height is None:
		return image

	if width is None:
		r = height / float(h)
		dim = (int(w * r), height)
	else:
		r = width / float(w)
		dim = (width, int(h * r))
	resized = cv.resize(image, dim, interpolation = inter)
	return resized

def findinscreen_pm(screen,pattern_name):
    template,_,_ = patterns[pattern_name]
    template = cv.cvtColor(template, cv.COLOR_BGR2GRAY)
    template = cv.Canny(template, 50, 200)
    (tH, tW) = template.shape[:2]
    image = screen
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    found = None
    # loop over the scales of the image
    for scale in np.linspace(0.2, 1.0, 20)[::-1]:
        resized = resize(gray, width = int(gray.shape[1] * scale))
        r = gray.shape[1] / float(resized.shape[1])
        if resized.shape[0] < tH or resized.shape[1] < tW:
                break
        edged = cv.Canny(resized, 50, 200)
        result = cv.matchTemplate(edged, template, cv.TM_CCOEFF)
        (_, maxVal, _, maxLoc) = cv.minMaxLoc(result)
        if found is None or maxVal > found[0]:
            found = (maxVal, maxLoc, r)
    (_, maxLoc, r) = found
    (startX, startY) = (int(maxLoc[0] * r), int(maxLoc[1] * r))
    (endX, endY) = (int((maxLoc[0] + tW) * r), int((maxLoc[1] + tH) * r))
    return ((startX,startY),(endX,endY))



