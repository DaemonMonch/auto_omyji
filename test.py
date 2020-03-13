import numpy as np
import cv2

img = cv2.imread('jjtp.png')
img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

thresh = cv2.Canny(img,140,200)

contours,h = cv2.findContours(thresh,1,2)
i = 0
for cnt in contours:
    pre = cv2.arcLength(cnt,True)
    if pre < 500:
        continue
    approx = cv2.approxPolyDP(cnt,0.01*pre,True)
    if len(approx)==4:
        i += 1
        cv2.drawContours(img,[cnt],0,(0,255,100),-1)
print(i)
cv2.imwrite('res.png',img)
