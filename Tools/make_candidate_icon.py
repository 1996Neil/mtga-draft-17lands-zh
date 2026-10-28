"""Deterministic high-resolution icon; no network assets or game modifications."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
out=Path(__file__).resolve().parents[1]/'resources/icons';out.mkdir(exist_ok=True)
size=1024
base=Image.new('RGBA',(size,size));d=ImageDraw.Draw(base)
for y in range(78,946):
 t=(y-78)/868
 color=tuple(int(a*(1-t)+b*t) for a,b in zip((31,72,97),(9,24,40)))+(255,)
 d.line((78,y,945,y),fill=color)
mask=Image.new('L',(size,size));ImageDraw.Draw(mask).rounded_rectangle((78,78,946,946),radius=198,fill=255);base.putalpha(mask)
d=ImageDraw.Draw(base);d.rounded_rectangle((80,80,944,944),radius=196,outline=(85,136,158,255),width=4)
for angle,cx,cy,color in [( -20,403,520,(206,216,219)),(0,513,482,(241,236,221)),(18,611,501,(45,118,145))]:
 card=Image.new('RGBA',(440,610));p=ImageDraw.Draw(card)
 p.rounded_rectangle((14,14,426,596),radius=40,fill=color+(255,),outline=(233,191,100,255),width=9)
 p.rounded_rectangle((45,45,395,565),radius=23,outline=(255,255,255,100),width=3)
 if angle==18:
  font=ImageFont.truetype('/System/Library/Fonts/SFNS.ttf',205)
  p.text((220,199),'17',font=font,fill=(250,246,231),anchor='mm')
  p.line((106,410,183,358,249,388,331,285),fill=(244,198,95),width=23)
  p.polygon([(331,285),(326,352),(272,308)],fill=(244,198,95))
 rotated=card.rotate(-angle,resample=Image.Resampling.BICUBIC,expand=True)
 base.alpha_composite(rotated,(int(cx-rotated.width/2),int(cy-rotated.height/2)))
base.save(out/'draft.png');base.save(out/'draft.icns',sizes=[(16,16),(32,32),(64,64),(128,128),(256,256),(512,512),(1024,1024)])
base.resize((256,256),Image.Resampling.LANCZOS).save(out/'preview.png')
