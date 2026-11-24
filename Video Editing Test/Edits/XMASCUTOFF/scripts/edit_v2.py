import json, os
L=os.path.expanduser("~/Documents/LuxeLight BROLL Folders/")
W=os.path.expanduser("~/.video-editing-work/luxe-light/xmas-cutoff-heygen/")
HG=W+"heygen_full.mp4"
caps="""16.80 so I've had a few of these
18.52 and honestly
19.44 it's a fair thing to worry about
21.00 because there are a lot of
22.24 copycat LuxeLights
23.20 going around right now
24.44 let me quickly show you
25.64 how to make sure you get the real one
27.38 because I learned this the hard way
29.08 first
30.26 only ever buy from
31.30 the official LuxeLight store
32.84 using the link on this video
34.30 those cheap marketplace listings
36.22 the $5 ones
37.42 that's where the fakes are
38.82 and the real one
39.82 is genuinely brilliant
41.72 this 230-degree beam
43.48 lights up everything in front of you
45.28 not just one little spot
46.84 click the wave sensor on
48.08 and it works every time
49.54 you just wave your hand
50.82 perfect when your hands are full
52.42 and it charges with USB-C
54.62 no batteries
55.74 here's how you know it's real
56.94 only the real one
58.32 switches from white light
59.42 to red light
60.30 and only the real one comes in
61.88 limited edition
62.54 pink
62.90 and orange
63.70 the fakes have neither
65.16 they dim
66.10 they flicker
66.78 and the wave sensor does nothing
68.56 I got my husband the real one in black
70.58 and he has not taken it off since
72.72 taking the bins out
73.96 walking the dog
75.00 off to work at 5am
76.28 I even went back
77.30 and got a few more
78.12 for the rest of the men in the family
79.70 a camo
80.28 and an orange
80.90 and a pink one for me
82.22 so don't let the fakes put you off
84.14 the real ones are worth it
86.18 every real LuxeLight
87.16 comes with a free carry case
88.70 and the more you get
89.56 the more you save
90.54 order by the 12th of December
91.96 and it's guaranteed for Christmas
93.70 just tap Shop Now on this video
95.52 so you know you're getting the real one"""
captions=[dict(t=float(l.split(" ",1)[0]), text=l.split(" ",1)[1]) for l in caps.split("\n")]
T=dict(clip=HG, src_in=0, talk=True)
def s(t, clip, src_in, **k): return dict(t=t, clip=L+clip, src_in=src_in, **k)
shots=[dict(T,t=16.80),
 s(21.00,"Fakes/hf_20261008_121416_7b9e65c5-f568-4817-8acb-e1a3fddcd9d6.mp4",0.3,bw=True),
 dict(T,t=24.44),
 s(25.64,"Fakes/IMG_8655.mov",3.53),
 dict(T,t=27.38),
 s(30.26,"Packaging/IMG_2731.MOV",4.83),
 dict(T,t=32.84),
 s(34.30,"Reviews/ScreenRecording_11-06-2026 16-40-25_1.MP4",1.6,zoom=1.22,blur=9),
 s(37.42,"Fakes/IMG_8637.mov",9.3,zoom=1.25,bw=True),
 dict(T,t=38.82),
 s(41.72,"In Hands/IMG_2729.MOV",7.53),
 s(43.48,"Colour Swatches/IMG_6596.MOV",1.87,mute=False),
 s(45.28,"Vs Other Headtorch/LuxeLight_body_2.mp4",4.87,speed=0.9),
 s(46.84,"Outside Torch DARK/snaptik_7461349711644069152_v2 (1).mp4",30.73,speed=1.3),
 s(48.08,"Red Light/04RedLight.mp4",3.0),
 s(49.54,"Wave Sensor/IMG_2548.MOV",0.23,speed=1.5),
 s(50.82,"Wave Sensor/Snaptik.app_7441625542597594400.mp4",0),
 s(52.42,"Charging/IMG_9981.MOV",3.67,speed=1.2,mute=False),
 dict(T,t=55.74),
 s(56.94,"In Hands/IMG_1717.mov",3.97),
 s(58.32,"Red Light/IMG_6618.MOV",12.4,mute=False),
 s(60.30,"Colour Swatches/hf_20260929_141355_034b7f1f-a858-4027-9015-616d77368d0d.mp4",0,speed=1.1),
 s(62.54,"Colour Swatches/IMG_8584.mov",3.17),
 s(62.90,"Colour Swatches/IMG_8585.mov",15.13),
 s(63.70,"Fakes/IMG_8641.mov",6.6,zoom=1.8,bw=True),
 s(65.16,"Fakes/hf_20261002_100835_cdb7d2ef-a701-49de-a516-688da640debd.mp4",1.6,bw=True),
 s(66.78,"Fakes/hf_20261002_114903_5b398124-73bf-4bb8-a8b0-73a60bd5db27.mp4",0.7,zoom=1.14,bw=True),
 dict(T,t=68.56),
 s(70.58,"Wave Sensor/IMG_0359.mp4",29.50),
 s(72.72,"Outside Torch DARK/IMG_8269 (1).mov",13.53),
 s(73.96,"Dog Walkers/LuxeLight - Dog Walking - No Subs.mov",31.03),
 s(75.00,"IMG_7946.mov",48.53),
 dict(T,t=76.28),
 s(78.12,"Xmas/IMG_3321.mov",8.80),
 s(79.70,"Colour Swatches/hf_20261028_220512_ffee63ef-9440-49c2-ad14-98848f361564.mp4",2.3),
 s(80.28,"Colour Swatches/IMG_6589.MOV",13.17,mute=False),
 s(80.90,"Colour Swatches/IMG_6576.MOV",1.0),
 dict(T,t=82.22),
 s(86.18,"Case/LuxeLight - V2 - B-roll - No-Subs.mov",52.53),
 s(88.70,"Xmas/IMG_3313.mov",2.80),
 s(90.54,"Xmas/IMG_6684.mov",1.37),
 s(93.70,"Red Light/IMG_8695.mov",4.17)]
e=dict(code="XMASCUTOFF", vo=W+"inputs/vo.mp3",
 hook_card=os.path.expanduser("~/.video-editing-work/luxe-light/fake-check-vo/black_bg.mp4"),
 hooks={"A":[0.0,5.45],"C":[5.48,10.46],"E":[10.5,16.72]}, body=[16.76,97.44], cuts=[], inserts=[],
 end_box={"at":"just tap Shop Now on this video","stack":["SHOP NOW FOR\nUP TO 61% OFF \U0001F381","60-DAY GUARANTEE \u2705"],"seq":[{"at":"just tap Shop Now on this video","boxes":["SHOP NOW FOR\nUP TO 61% OFF \U0001F381","60-DAY GUARANTEE \u2705"]}]},
 click=os.path.expanduser("~/Video Editing Test/Assets/Click_Mouse_Click_02.mp3"),
 captions=captions, shots=shots,
 hook_shots={"A":[dict(T,t=0.0)],
  "C":[dict(t=5.52,clip=L+"Packaging/IMG_1718.mov",src_in=2.13,zoom=1.35,y=0.3), dict(T,t=8.30)],
  "E":[dict(t=10.54,clip=L+"In Hands/IMG_2618.MOV",src_in=0), dict(t=13.06,clip=L+"Red Light/07RedLight.mp4",src_in=1.9)]},
 hook_captions={"A":[],"C":[],"E":[]},
 hook_text={"A":[],"C":["WIVES: don't make","my mistake \U0001F62B"],"E":["I almost gave","him a FAKE \U0001F633"]},
 hook_image={"A":{"path":W+"reply.png","width":640,"top":1010}})
json.dump(e,open(W+"edit.json","w"),indent=1)
