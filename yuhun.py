import numpy as np
from ppadb.client import Client as AdbClient
from multiprocessing import Process,Pipe
import random as rd
import cv2 as cv
import time
import img

client = AdbClient(host="127.0.0.1", port=5037)
devices = client.devices()
mode = 'slave'
master = None
slave = None
device_shape = {}
tiaozhan_pts = None
def screencap(device,times = 1,duration=0):
    res = None
    cap_duration_ms = 0
    for i in range(0,times):
        res=device.screencap()
        if duration > 0:
            time.sleep(duration)
    res = np.asarray(res,dtype=np.uint8)

    return cv.imdecode(res,0)



for d in devices:
    sc = screencap(d,duration=0)
    h,w = sc.shape
    print('device {} shape {}',d,(w,h))
    tiaozhan_pts = img.findinscreen(sc,'tiaozhan')
    if tiaozhan_pts is not None:
        print('find master {}'.format(d))
        device_shape[d] = (w,h,'master')
        master = d
    else:
        print('find slave {}'.format(d))
        device_shape[d] = (w,h,'slave')
        slave = d


if len(devices) == 0:
    print('adb fail')
    exit(-1)

if len(devices) == 2:
    mode = 'master_slave'
    

def click(device,top_leftX,top_leftY,bottom_rightX,bottom_rightY):
    delta = 5
    if top_leftX == 0:
        top_leftX = delta
    if top_leftY == 0:
        top_leftY = delta
    w,h,who = device_shape[device]    
    if bottom_rightX > w:
        bottom_rightX = w
    if bottom_rightY > h:
        bottom_rightY = h
        
    pos = 'input tap {} {}'.format(rd.randrange(int(top_leftX),int(bottom_rightX) - delta),rd.randrange(int(top_leftY),int(bottom_rightY) - delta))
    print(who + ' ' + pos)
    device.shell(pos)

def clickpos(device,x,y):
    pos = 'input tap {} {}'.format(x,y)
    _,_,who = device_shape[device]
    print(who + ' ' + pos)
    device.shellpos()


def click0(device,pts):
    pts = np.int32(pts)
    click(device,pts[0][0][0],pts[0][0][1],pts[2][0][0],pts[2][0][1])


def sleep(min = 0.02,max = 0.2):
    t = rd.uniform(min,max)
    print('sleep {}s'.format(t))
    time.sleep(t)

def master_sm(device,pip):
    #0 --> zudui  1 -->fighting 
    s = 0
    r = 0
    pts = img.findinscreen(screencap(device),'tiaozhan',0.7)
    print('master tiaozhan {}'.format(pts))

    w,h,_ = device_shape[device]
    if pts is not None:
        click0(device,pts)
        sleep(min=10,max=15)
    while True:
        if s == 0:
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
                    print('master detect fight is over,notify slave and wait slave notify')
                    pip.send(0)
                    pip.recv()
                    click(device,w*0.6,h*0.75,w,h)
                    click(device,w*0.6,h*0.75,w,h)
                    click(device,w*0.6,h*0.75,w,h)
                    sleep(min=2,max=3)
                    for i in range(0,rd.randint(3,4)):
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
                        click0(device,pts)
                        s = 0
                        r = r + 1
                        print('round ',r)
                        break
               
def checkPts(pts):
    w = np.where(pts < 0)
    return len([x for x in filter(lambda x: x.size >0,w)]) == 0

def slave_sm(device,pip):
#0 --> zudui 1 -->fighting 
    s = 0
    while True:
        is_click = False
        if s == 0:
            scr = screencap(device)
            pts = img.findinscreen(scr,'zidong',0.8)
            if pts is None:
                if pip:
                    print('slave detect fight is over,notify master and wait master notify')
                    pip.send(0)
                    pip.recv()
                w,h,_ = device_shape[device]
                click(device,w*0.6,h*0.8,w,h*0.85)
                click(device,w*0.6,h*0.8,w,h*0.85)
                click(device,w*0.6,h*0.8,w,h*0.85)
                sleep(min=2,max=3)
                for i in range(0,rd.randint(3,4)):
                    click(device,w*0.6,h*0.8,w,h*0.85)
                    is_click = True
                    #sleep(min=1 ,max=1.5)
            if is_click:
                sleep(min=10,max=15)
                print('slave to zudui s ---> 1')
                s = 1

        elif s == 1:
            pts = img.findinscreen(screencap(device),'zidong',0.8)
            if pts is not None:
                print('slave to fight s ---> 0')
                s = 0

slave_p = None
master_p = None
mp,sp = Pipe()
if slave:
    #mode = 'single' if master else 'single'
    slave_p = Process(target=slave_sm,args=(slave,sp if master else None))
    slave_p.start()    
if master:
    master_p=Process(target=master_sm,args=(master,mp))
    master_p.start()
if slave_p:
    slave_p.join()
if master_p:
    master_p.join()


