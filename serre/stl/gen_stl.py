# Genere des STL equivalents aux pieces Fusion (sans petits trous) pour tester le temps au slicer.
import numpy as np, sys
from stl import mesh
L,W,H,WALL,FLOOR,JEU,TOIT_H,FEN=100,70,28,1.6,1.2,0.3,6,8
def box(x,y,z,w,d,h):
    v=np.array([[x,y,z],[x+w,y,z],[x+w,y+d,z],[x,y+d,z],[x,y,z+h],[x+w,y,z+h],[x+w,y+d,z+h],[x,y+d,z+h]],float)
    f=[[0,3,1],[1,3,2],[4,5,7],[5,6,7],[0,1,4],[1,5,4],[1,2,5],[2,6,5],[2,3,6],[3,7,6],[3,0,7],[0,4,7]]
    return v,f
def save(name,boxes):
    tris=[]
    for b in boxes:
        v,f=box(*b); tris+= [v[i] for i in f]
    m=mesh.Mesh(np.zeros(len(tris),dtype=mesh.Mesh.dtype)); m.vectors[:]=np.array(tris); m.save(name)
def hollow(x,y,w,d,h,t=WALL,fl=FLOOR):
    return [(x,y,0,w,d,fl),(x,y,fl,w,t,h-fl),(x,y+d-t,fl,w,t,h-fl),(x,y+t,fl,t,d-2*t,h-fl),(x+w-t,y+t,fl,t,d-2*t,h-fl)]
save('Base_bac.stl',hollow(0,0,L,W,H))
tw,td=L+2*(WALL+JEU),W+2*(WALL+JEU)
ring=[(0,0,0,tw,WALL,TOIT_H),(0,td-WALL,0,tw,WALL,TOIT_H),(0,WALL,0,WALL,td-2*WALL,TOIT_H),(tw-WALL,WALL,0,WALL,td-2*WALL,TOIT_H)]
top=[(0,0,TOIT_H,tw,FEN,1.2),(0,td-FEN,TOIT_H,tw,FEN,1.2),(0,FEN,TOIT_H,FEN,td-2*FEN,1.2),(tw-FEN,FEN,TOIT_H,FEN,td-2*FEN,1.2)]
save('Toit_cadre.stl',ring+top)
save('Boitier_Nano.stl',hollow(0,0,45+2*WALL,25+2*WALL,18))
save('Support_capteurs.stl',[(0,0,0,90,10,2.4)])
