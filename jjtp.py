import numpy as np
from ppadb.client import Client as AdbClient
from multiprocessing import Process
import random as rd
import cv2 as cv
import time
import img

client = AdbClient(host="127.0.0.1", port=5037)
devices = client.devices()
device_shape = {}

if len(devices) == 0:
    print('adb fail')
    exit(-1)
device = devices[0]

def click(device,top_leftX,top_leftY,bottom_rightX,bottom_rightY):
    delta = 5
    if top_leftX == 0:
        top_leftX = delta
    if top_leftY == 0:
        top_leftY = delta
    w,h = device_shape[device]    
    if bottom_rightX > w:
        bottom_rightX = w
    if bottom_rightY > h:
        bottom_rightY = h
        
    pos = 'input tap {} {}'.format(rd.randrange(int(top_leftX),int(bottom_rightX) - delta),rd.randrange(int(top_leftY),int(bottom_rightY) - delta))
    print(pos)
    device.shell(pos)

def clickpos(device,x,y):
    print(x,y)
    device.shell('input tap {} {}'.format(x,y))


def screencap(device):
    res=device.screencap()
    res = np.asarray(res,dtype=np.uint8)
    return cv.imdecode(res,0)

def click0(device,pts):
    pts = np.int32(pts)
    click(device,pts[0][0][0],pts[0][0][1],pts[2][0][0],pts[2][0][1])


def sleep(min = 0.02,max = 0.2):
    t = rd.uniform(min,max)
    print('sleep {}s'.format(t))
    time.sleep(t)

def master_sm(device):
    
    #0 --> jjtp  1 -->click user to find jingong 2 --> fight 3 --> no user to refresh
    s = 0
    user = None
    while True:
        if s == 0:
            users = find_user(screencap(device))
            if user is not None:
                s = 1
        elif s == 1:
            # 
            for user in users:
                while True:
                    if s == 1:
                        pts_1 = img.findinscreen(screencap(device),'zidong',0.8)
                        if pts_1 is not None:
                            print('master fighting s ---> 1')
                            s = 1
                    elif s == 1:
                        #sleep(min=20,max=27)
                        while True:
                            is_click = False
                            sc = screencap(device)
                            zidong_pts = img.findinscreen(sc,'zidong',0.8)
                            if zidong_pts is None:
                                click(device,w*0.6,h*0.75,w,h)
                                click(device,w*0.6,h*0.75,w,h)
                                click(device,w*0.6,h*0.75,w,h)
                                sleep(min=2,max=3)
                                for i in range(0,rd.randint(2,3)):
                                    click(device,w*0.6,h*0.75,w,h)
                                    #sleep(min=1 ,max=3)
                                is_click = True    
                            #for i in range(0,rd.randint(3,5)):
                            #    click(device,w*0.12,h*0.15,w*0.8,h*0.75)
                            #    sleep(min=1 ,max=1.5)


                            if is_click:
                                sleep(min=10,max=15)
                                pts = img.findinscreen(screencap(device),'tiaozhan',0.7)
                                if pts is not None:
                                    print('master fight finish s ---> 0')
                                    click0(device,pts)
                                    s = 0
                                    r = r + 1
                                    print('round ',r)
                                    break
        else:
            refresh = img.findinscreen(screencap(device),'shuaxin')
            if refresh is None:
                print('refresh button unavailable wait...')
                sleep(min=10,max=15)

