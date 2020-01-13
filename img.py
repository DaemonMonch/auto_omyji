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

    if len(good)>MIN_MATCH_COUNT:
#        cv.imwrite('{}.png'.format(rd.randint(0,1000)),screen)
        src_pts = np.float32([ img_kp[m.queryIdx].pt for m in good ]).reshape(-1,1,2)
        dst_pts = np.float32([ k[m.trainIdx].pt for m in good ]).reshape(-1,1,2)
        M, mask = cv.findHomography(src_pts, dst_pts, cv.RANSAC,5.0)
        matchesMask = mask.ravel().tolist()
        h,w = img.shape
        pts = np.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2)
        dst = cv.perspectiveTransform(pts,M)
        print('find img in {} ms'.format(int(time.time() * 1000 - st)))
        return dst
    print('find {} in {} ms'.format(pattern_name,int(time.time() * 1000 - st)))
    return None



