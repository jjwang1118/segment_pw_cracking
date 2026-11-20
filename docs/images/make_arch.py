#!/usr/bin/env python3
# Two-stage training architecture diagram -> local PNG via cairosvg. No network.
import math, cairosvg

SANS = "DejaVu Sans, sans-serif"
MONO = "DejaVu Sans Mono, monospace"

FG="#1c1b19"; MUT="#6b675f"; BORD="#c9c3b7"
ARROW="#6b675f"
DATA="#0f766e"; DATA_F="#e4f2f0"
S1="#3b5bdb";  S1_F="#eef1fd"
S2="#c2560f";  S2_F="#fbeadd"
EVAL="#15803d";EVAL_F="#e8f5ec"
ART="#8a857b"
MODB="#b9b3a7"

el=[]
def add(s): el.append(s)

def box(x,y,w,h,title,sub=None,fill="#ffffff",stroke=BORD,sw=1.5,rx=11,
        tcol=FG,tsize=15,center=False,badge=None,bcol=None):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    if badge is not None:
        bx,by=x+24,y+h/2
        add(f'<circle cx="{bx}" cy="{by}" r="14" fill="{bcol}"/>')
        add(f'<text x="{bx}" y="{by+5.5}" font-family="{MONO}" font-size="15" '
            f'font-weight="700" fill="#ffffff" text-anchor="middle">{badge}</text>')
        tx0=x+46
    else:
        tx0=x+16
    cx=x+w/2
    if center:
        if sub:
            add(f'<text x="{cx}" y="{y+h/2-2}" font-family="{SANS}" font-size="{tsize}" font-weight="700" fill="{tcol}" text-anchor="middle">{title}</text>')
            add(f'<text x="{cx}" y="{y+h/2+15}" font-family="{MONO}" font-size="10" fill="{MUT}" text-anchor="middle">{sub}</text>')
        else:
            add(f'<text x="{cx}" y="{y+h/2+5}" font-family="{SANS}" font-size="{tsize}" font-weight="700" fill="{tcol}" text-anchor="middle">{title}</text>')
    else:
        if sub:
            add(f'<text x="{tx0}" y="{y+h/2-2}" font-family="{SANS}" font-size="{tsize}" font-weight="700" fill="{tcol}">{title}</text>')
            add(f'<text x="{tx0}" y="{y+h/2+15}" font-family="{MONO}" font-size="10" fill="{MUT}">{sub}</text>')
        else:
            add(f'<text x="{tx0}" y="{y+h/2+5}" font-family="{SANS}" font-size="{tsize}" font-weight="700" fill="{tcol}">{title}</text>')

def head(x2,y2,ux,uy,col,size=8):
    px,py=-uy,ux
    bx,by=x2-ux*size, y2-uy*size
    p1=(bx+px*size*0.55, by+py*size*0.55); p2=(bx-px*size*0.55, by-py*size*0.55)
    add(f'<path d="M{x2:.1f} {y2:.1f} L{p1[0]:.1f} {p1[1]:.1f} L{p2[0]:.1f} {p2[1]:.1f} Z" fill="{col}"/>')

def arrow(pts,col=ARROW,dash=False,sw=2):
    d="M"+" L".join(f"{x:.1f} {y:.1f}" for x,y in pts)
    da=' stroke-dasharray="5 4"' if dash else ''
    add(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{sw}"{da}/>')
    (x1,y1),(x2,y2)=pts[-2],pts[-1]
    L=math.hypot(x2-x1,y2-y1) or 1
    head(x2,y2,(x2-x1)/L,(y2-y1)/L,col)

def note(x,y,t,col=MUT,size=9.5,anchor="start"):
    add(f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" fill="{col}" text-anchor="{anchor}">{t}</text>')

# ---- title ----
add(f'<text x="24" y="40" font-family="{SANS}" font-size="23" font-weight="700" fill="{FG}">Two-Stage Training Architecture</text>')
add(f'<text x="24" y="62" font-family="{SANS}" font-size="12.5" fill="{MUT}">Two data sources  &#8594;  plaintext / JSON preprocessing  &#8594;  two-stage training  &#8594;  evaluation</text>')

cxm=162; bw=212; bx=56

# ========== LEFT pipeline A : PLAINTEXT source (no module) ==========
box(bx,96,bw,46,"Raw passwords","datasets/*.txt · plaintext",center=True,tsize=14,stroke=ART)
box(bx,168,bw,46,"Clean / filter","dedup · strip-test · length/charset",center=True,tsize=14)
box(bx,266,bw,50,"Plaintext corpus","≈ 2.74M rows",fill=DATA_F,stroke=DATA,sw=2,center=True,tsize=14,tcol=DATA)
arrow([(cxm,142),(cxm,168)])                 # Raw -> Clean
arrow([(cxm,214),(cxm,266)])                 # Clean -> Plaintext corpus
note(cxm+8,250,"plaintext")

# ========== LEFT pipeline B : JSON source -> module(Split+Tag) ==========
box(bx,330,bw,42,"JSON data","sibling · pii · others",center=True,tsize=14,stroke=ART)
# module wraps Split + Tag
MX,MY,MW,MH=24,398,276,122
add(f'<rect x="{MX}" y="{MY}" width="{MW}" height="{MH}" rx="16" fill="#fbfaf7" '
    f'stroke="{MODB}" stroke-width="1.8" stroke-dasharray="7 5"/>')
add(f'<rect x="{MX+14}" y="{MY-15}" width="112" height="30" rx="15" fill="{DATA}"/>')
add(f'<text x="{MX+27}" y="{MY+5}" font-family="{SANS}" font-size="12.5" font-weight="700" fill="#ffffff">Split + Tag</text>')
box(bx,412,bw,38,"Split","segment into tokens",center=True,tsize=13)
box(bx,468,bw,38,"Tag","PCFG · semantic-guesser",center=True,tsize=13)
# output of the module
box(bx,536,bw,48,"Conditional data","JSON · split + tagged",fill=DATA_F,stroke=DATA,sw=2,center=True,tsize=13,tcol=DATA)
arrow([(cxm,372),(cxm,412)])                 # JSON data -> Split (into module)
arrow([(cxm,450),(cxm,468)])                 # Split -> Tag
arrow([(cxm,506),(cxm,536)])                 # Tag -> Conditional data (out of module)
note(cxm+8,528,"JSON")

# ================= RIGHT: two-stage training =================
cxt=520; tw=320; tx=cxt-tw/2   # 360
box(tx,96,tw,46,"Base LLM","Mistral-7B · Qwen3-4B",stroke=ART,tcol=FG)
box(tx,250,tw,82,"Plaintext Distribution Learning","full fine-tune · no LoRA · learn p(password)",
    fill=S1_F,stroke=S1,sw=2.4,rx=13,badge="2",bcol=S1,tsize=15)
box(tx,397,tw,46,"Distribution model","stage-1 output · final/",stroke=ART)
box(tx,519,tw,82,"Conditional Targeted Fine-tuning","QLoRA · tags → password · loss on password",
    fill=S2_F,stroke=S2,sw=2.4,rx=13,badge="3",bcol=S2,tsize=15)
box(tx,615,tw,46,"Final model","lora_final + adapter_config",stroke=ART)
box(tx,681,tw,64,"Evaluation","crack rate @1 / 10 / 100 / 1000",
    fill=EVAL_F,stroke=EVAL,sw=2.4,rx=13,badge="4",bcol=EVAL,tsize=15)

arrow([(cxt,142),(cxt,250)])                 # Base -> 2
arrow([(cxt,332),(cxt,397)])                 # 2 -> Dist model
arrow([(cxt,443),(cxt,519)],col=S2,dash=True)# Dist -> 3 (weight reuse)
add(f'<text x="{cxt+10}" y="485" font-family="{SANS}" font-size="10.5" fill="{S2}">stage-1 weights as base</text>')
arrow([(cxt,601),(cxt,615)])                 # 3 -> Final
arrow([(cxt,661),(cxt,681)])                 # Final -> Eval

# data feeds: module outputs -> stages (horizontal)
arrow([(bx+bw,291),(tx,291)],col=DATA,sw=2)  # Plaintext corpus -> 2  (2 cy=291)
arrow([(bx+bw,560),(tx,560)],col=DATA,sw=2)  # Conditional data -> 3  (3 cy=560)
note((bx+bw+tx)/2,285,"plaintext",col=DATA,anchor="middle")
note((bx+bw+tx)/2,554,"JSON",col=DATA,anchor="middle")

# ================= legend =================
ly=784
items=[(DATA,"Data"),(S1,"Stage 1  full FT"),(S2,"Stage 2  LoRA"),(EVAL,"Eval")]
lx=24
for col,lab in items:
    add(f'<rect x="{lx}" y="{ly-11}" width="12" height="12" rx="3" fill="{col}"/>')
    add(f'<text x="{lx+18}" y="{ly}" font-family="{SANS}" font-size="12" fill="{MUT}">{lab}</text>')
    lx+= 34 + len(lab)*7.2
lx=int(lx)
add(f'<line x1="{lx}" y1="{ly-4}" x2="{lx+28}" y2="{ly-4}" stroke="{S2}" stroke-width="2" stroke-dasharray="5 4"/>')
add(f'<text x="{lx+36}" y="{ly}" font-family="{SANS}" font-size="12" fill="{MUT}">weight reuse</text>')

W,H=760,806
svg=(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
     f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>' + "".join(el) + '</svg>')

base="/work/u4996812/tmp/claude-43574/-home-u4996812-llm-pcfg-cracking/bd00bf48-28fd-4a66-9301-c50822ea5478/scratchpad/two_stage_arch"
open(base+".svg","w").write(svg)
cairosvg.svg2png(bytestring=svg.encode(),write_to=base+".png",output_width=W*2,output_height=H*2,background_color="#ffffff")
print("wrote",base+".png")
