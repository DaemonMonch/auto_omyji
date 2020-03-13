import cv2 as cv
import numpy as np


def resize(image, width = None, height = None, inter = cv.INTER_AREA):
	# initialize the dimensions of the image to be resized and
	# grab the image size
	dim = None
	(h, w) = image.shape[:2]

	# if both the width and height are None, then return the
	# original image
	if width is None and height is None:
		return image

	# check to see if the width is None
	if width is None:
		# calculate the ratio of the height and construct the
		# dimensions
		r = height / float(h)
		dim = (int(w * r), height)

	# otherwise, the height is None
	else:
		# calculate the ratio of the width and construct the
		# dimensions
		r = width / float(w)
		dim = (width, int(h * r))

	# resize the image
	resized = cv.resize(image, dim, interpolation = inter)

	# return the resized image
	return resized

template = cv.imread('patterns/jjtp_c.png')
template = cv.cvtColor(template, cv.COLOR_BGR2GRAY)
template = cv.Canny(template, 50, 200)
(tH, tW) = template.shape[:2]
image = cv.imread('jjtp.png')
gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
found = None
founds = []
        # loop over the scales of the image
for scale in np.linspace(0.2, 1.0, 20)[::-1]:
# resize the image according to the scale, and keep track
                # of the ratio of the resizing
    resized = resize(gray, width = int(gray.shape[1] * scale))
    r = gray.shape[1] / float(resized.shape[1])
          
    # if the resized image is smaller than the template, then break
                    # from the loop
    if resized.shape[0] < tH or resized.shape[1] < tW:
            break

    # detect edges in the resized, grayscale image and apply template
    # matching to find the template in the image
    edged = cv.Canny(resized, 50, 200)
    result = cv.matchTemplate(edged, template, cv.TM_CCOEFF)
    (_, maxVal, _, maxLoc) = cv.minMaxLoc(result)

    # if we have found a new maximum correlation value, then ipdate
    # the bookkeeping variable
    #if found is None or maxVal > found[0]:
    found = (maxVal, maxLoc, r)
    founds.append(found)
    # unpack the bookkeeping varaible and compute the (x, y) coordinates
    # of the bounding box based on the resized ratio
for found in founds:
    (_, maxLoc, r) = found
    (startX, startY) = (int(maxLoc[0] * r), int(maxLoc[1] * r))
    (endX, endY) = (int((maxLoc[0] + tW) * r), int((maxLoc[1] + tH) * r))

    # draw a bounding box around the detected result and display the image
    cv.rectangle(image, (startX, startY), (endX, endY), (0, 0, 255), 2)
cv.imwrite("res.png", image)
