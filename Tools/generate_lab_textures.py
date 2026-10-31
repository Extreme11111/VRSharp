from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import math,random
out=Path('ArtSource/VRSharpLab/Textures')
fontpath='C:/Windows/Fonts/consola.ttf'
for variant in range(3):
 random.seed(42+variant)
 im=Image.new('RGB',(2048,1024),(3,10,19)); d=ImageDraw.Draw(im)
 f=ImageFont.truetype(fontpath,22); small=ImageFont.truetype(fontpath,16); big=ImageFont.truetype(fontpath,36)
 cyan=(66,184,239); dim=(16,62,88); white=(160,216,234); amber=(250,128,55)
 for x in range(0,2048,32):d.line((x,0,x,1024),fill=(7,23,35))
 for y in range(0,1024,32):d.line((0,y,2048,y),fill=(7,23,35))
 d.rectangle((18,18,2030,1006),outline=cyan,width=3)
 title=['NEXUS / CONTAINMENT ARRAY','SYNAPTIC FIELD / TELEMETRY','ROBOTICS / DIAGNOSTIC CORE'][variant]
 d.text((48,35),title,font=big,fill=white);d.text((1530,45),'LAB 07 / ONLINE',font=f,fill=cyan)
 for box in [(40,110,470,770),(490,110,1520,770),(1540,110,2006,770),(40,790,2006,970)]:d.rectangle(box,outline=dim,width=3)
 cx,cy=1005,440
 for r in (100,210,280):d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=cyan if r==280 else dim,width=2)
 pts=[]
 for i in range(90):
  a=random.uniform(0,math.tau); r=270*math.sqrt(random.random());pts.append((cx+math.cos(a)*r,cy+math.sin(a)*r))
 for a in pts:
  for b in sorted(pts,key=lambda p:(p[0]-a[0])**2+(p[1]-a[1])**2)[1:4]:d.line((*a,*b),fill=(34,96,134),width=1)
  d.ellipse((a[0]-3,a[1]-3,a[0]+3,a[1]+3),fill=white)
 for j in range(16):
  y=135+j*36;d.text((60,y),f'CH {j+1:02d}  {random.uniform(12,99):06.2f}  STABLE',font=small,fill=white)
  d.rectangle((320,y+7,430,y+16),outline=dim);d.rectangle((322,y+9,322+random.randrange(20,100),y+14),fill=cyan)
 for j in range(12):
  y=140+j*48;d.text((1560,y),f'NODE {j+1:02d}  SYNC {random.randrange(91,100)}%',font=small,fill=cyan)
  d.line((1560,y+29,1980,y+29),fill=dim)
 for j in range(3):
  pts2=[(60+i*4,850+j*30+15*math.sin(i*.15+j)+6*math.sin(i*.53)) for i in range(480)]
  d.line(pts2,fill=cyan if j!=1 else amber,width=2)
 d.text((530,712),'FIELD INTEGRITY  99.98%     VACUUM  0.002 Pa',font=f,fill=cyan)
 im.save(out/f'T_LabUI_{variant}.png')
print('3 high resolution telemetry textures created')
