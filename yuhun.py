import numpy as np
from ppadb.client import Client as AdbClient
from multiprocessing import Process
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

device_metrics = {} #device_metrics[d] = dict(tm=False,ftpr=0)

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


def screencap(device,times = 1,duration=0.3):
    res = None
    cap_duration_ms = 0
    for i in range(0,times):
        res=device.screencap()
        if duration > 0:
            time.sleep(duration)
    res = np.asarray(res,dtype=np.uint8)

    return cv.imdecode(res,0)

def click0(device,pts):
    pts = np.int32(pts)
    click(device,pts[0][0][0],pts[0][0][1],pts[2][0][0],pts[2][0][1])


def sleep(min = 0.02,max = 0.2):
    t = rd.uniform(min,max)
    print('sleep {}s'.format(t))
    time.sleep(t)

tiaozhan_pts = None
for d in devices:
    device_metrics[d] = dict(tm=False,ftpr=0)
    st = time.time() * 1000
    sc = screencap(d,duration=0)
    cap_duration_ms = int(time.time() * 1000 - st)
    if cap_duration_ms > 2000:
        device_metrics[d]['tm'] = True
        print('device {} screen cap in {}ms switch to tm mode'.format(d,cap_duration_ms))
    h,w = sc.shape
    device_shape[d] = (w,h)
    print('device {} shape {}',d,(w,h))
    tiaozhan_pts = img.findinscreen(sc,'tiaozhan')
    if tiaozhan_pts is not None:
        print('find master {}'.format(d))
        master = d
    else:
        print('find slave {}'.format(d))
        slave = d

print('master',master)
print('slave',slave)
def master_sm(device,slave):
    #0 --> zudui  1 -->fighting 
    s = 0
    pts = tiaozhan_pts
    def cond():
        return True if slave is None else slave.is_alive()

    metrics = device_metrics[device]
    w,h = device_shape[device]
    while cond():
        if s == 0:
            if pts is not None:
                click0(device,pts)
                sleep(min=1,max=2)
            pts_1 = img.findinscreen(screencap(device),'zidong',0.7)
            if pts_1 is not None:
                pts = pts_1
                print('master fighting s ---> 1')
                s = 1
        elif s == 1:
            #sleep(min=20,max=27)
            while True:
                is_click = True
                sc = screencap(device)
                zidong_pts = img.findinscreen(sc,'zidong',0.7)
                if zidong_pts is None:
                    for i in range(0,rd.randint(4,6)):
                        click(device,w*0.6,h*0.7,w,h)
                        sleep(min=1 ,max=1.5)
                    is_click = True    
                    sleep(min=3,max=4)
                #for i in range(0,rd.randint(3,5)):
                #    click(device,w*0.12,h*0.15,w*0.8,h*0.75)
                #    sleep(min=1 ,max=1.5)


                if is_click:
                    pts = img.findinscreen(screencap(device),'tiaozhan',0.7)
                    if pts is not None:
                        print('master fight finish s ---> 0')
                        s = 0
                        break
               
def checkPts(pts):
    w = np.where(pts < 0)
    return len([x for x in filter(lambda x: x.size >0,w)]) == 0

def slave_sm(device):
#0 --> zudui 1 -->fighting 
    s = 0
    while True:
        print('slave cpu percent {}'.format(device.cpu_percent()))
        is_click = False
        if s == 0:
            scr = screencap(device)
            pts = img.findinscreen(scr,'zidong',0.7)
            if pts is None:
                w,h = device_shape[device]
                for i in range(0,rd.randint(4,6)):
                    click(device,w*0.6,h*0.7,w,h)
                    is_click = True
                    sleep(min=1 ,max=1.5)
            if is_click:
                sleep(min=7,max=9)
                print('slave to zudui s ---> 1')
                s = 1

        elif s == 1:
            pts = img.findinscreen(screencap(device),'zidong',0.7)
            if pts is not None:
                print('slave to fight s ---> 0')
                s = 0

slave_p = None
if slave:
    #mode = 'single' if master else 'single'
    slave_p = Process(target=slave_sm,args=(slave,))
    slave_p.start()    
if master:
    p=Process(target=master_sm,args=(master,slave_p))
    p.start()
    p.join()



