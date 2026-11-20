#!/usr/bin/env python3
# Horizontal (left-to-right), paper-ready two-stage architecture figure -> PNG. Local only.
import math, cairosvg

SANS="DejaVu Sans, sans-serif"; MONO="DejaVu Sans Mono, monospace"
FG="#1c1b19"; MUT="#6b675f"; BORD="#c9c3b7"; ARROW="#6b675f"
DATA="#0f766e"; DATA_F="#e4f2f0"
S1="#3b5bdb"; S1_F="#eef1fd"
S2="#c2560f"; S2_F="#fbeadd"
EVAL="#15803d"; EVAL_F="#e8f5ec"
ART="#8a857b"; MODB="#b9b3a7"

el=[]
def add(s): el.append(s)

def box(x,y,w,h,title,sub=None,fill="#ffffff",stroke=BORD,sw=1.5,rx=11,
        tcol=FG,tsize=14,center=True,badge=None,bcol=None,subsize=10):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    if badge is not None:
        add(f'<circle cx="{x+22}" cy="{y+22}" r="13" fill="{bcol}"/>')
        add(f'<text x="{x+22}" y="{y+26.5}" font-family="{MONO}" font-size="13" font-weight="700" fill="#fff" text-anchor="middle">{badge}</text>')
    cx=x+w/2
    if center:
        if sub:
            add(f'<text x="{cx}" y="{y+h/2-2}" font-family="{SANS}" font-size="{tsize}" font-weight="700" fill="{tcol}" text-anchor="middle">{title}</text>')
            add(f'<text x="{cx}" y="{y+h/2+14}" font-family="{MONO}" font-size="{subsize}" fill="{MUT}" text-anchor="middle">{sub}</text>')
        else:
            add(f'<text x="{cx}" y="{y+h/2+5}" font-family="{SANS}" font-size="{tsize}" font-weight="700" fill="{tcol}" text-anchor="middle">{title}</text>')
    else:
        tx0=x+(42 if badge is not None else 16)
        if sub:
            add(f'<text x="{tx0}" y="{y+h/2-2}" font-family="{SANS}" font-size="{tsize}" font-weight="700" fill="{tcol}">{title}</text>')
            add(f'<text x="{tx0}" y="{y+h/2+15}" font-family="{MONO}" font-size="{subsize}" fill="{MUT}">{sub}</text>')
        else:
            add(f'<text x="{tx0}" y="{y+h/2+5}" font-family="{SANS}" font-size="{tsize}" font-weight="700" fill="{tcol}">{title}</text>')

def stagebox(x,y,w,h,l1,l2,sub,fill,stroke,badge,bcol):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" stroke="{stroke}" stroke-width="2.4"/>')
    add(f'<circle cx="{x+24}" cy="{y+24}" r="14" fill="{bcol}"/>')
    add(f'<text x="{x+24}" y="{y+28.5}" font-family="{MONO}" font-size="14" font-weight="700" fill="#fff" text-anchor="middle">{badge}</text>')
    cx=x+w/2
    add(f'<text x="{cx}" y="{y+56}" font-family="{SANS}" font-size="15" font-weight="700" fill="{FG}" text-anchor="middle">{l1}</text>')
    add(f'<text x="{cx}" y="{y+76}" font-family="{SANS}" font-size="15" font-weight="700" fill="{FG}" text-anchor="middle">{l2}</text>')
    add(f'<text x="{cx}" y="{y+97}" font-family="{MONO}" font-size="9.5" fill="{MUT}" text-anchor="middle">{sub}</text>')

def head(x2,y2,ux,uy,col,size=8):
    px,py=-uy,ux; bx,by=x2-ux*size,y2-uy*size
    p1=(bx+px*size*0.55,by+py*size*0.55); p2=(bx-px*size*0.55,by-py*size*0.55)
    add(f'<path d="M{x2:.1f} {y2:.1f} L{p1[0]:.1f} {p1[1]:.1f} L{p2[0]:.1f} {p2[1]:.1f} Z" fill="{col}"/>')

def arrow(pts,col=ARROW,dash=False,sw=2):
    d="M"+" L".join(f"{x:.1f} {y:.1f}" for x,y in pts)
    da=' stroke-dasharray="6 4"' if dash else ''
    add(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{sw}"{da}/>')
    (x1,y1),(x2,y2)=pts[-2],pts[-1]; L=math.hypot(x2-x1,y2-y1) or 1
    head(x2,y2,(x2-x1)/L,(y2-y1)/L,col)

def note(x,y,t,col=MUT,size=10,anchor="start",font=MONO):
    add(f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" fill="{col}" text-anchor="{anchor}">{t}</text>')

def wrap(x,y,text,width_px,size=11,col=MUT,lh=15):
    cpl=max(10,int(width_px/(size*0.55)))
    words=text.split(); lines=[]; cur=""
    for w in words:
        if len(cur)+len(w)+1<=cpl: cur=(cur+" "+w).strip()
        else: lines.append(cur); cur=w
    if cur: lines.append(cur)
    for i,ln in enumerate(lines):
        add(f'<text x="{x}" y="{y+i*lh}" font-family="{SANS}" font-size="{size}" fill="{col}">{ln}</text>')
    return len(lines)

def eyebrow(x,y,t,col):
    add(f'<text x="{x}" y="{y}" font-family="{SANS}" font-size="11.5" font-weight="700" fill="{col}" letter-spacing="1.3">{t}</text>')

# ---------------- title ----------------
add(f'<text x="30" y="40" font-family="{SANS}" font-size="24" font-weight="700" fill="{FG}">Two-Stage Training Architecture</text>')
add(f'<text x="30" y="64" font-family="{SANS}" font-size="13" fill="{MUT}">Left-to-right overview: two data sources &#8594; preprocessing &#8594; plaintext distribution learning &#8594; conditional fine-tuning &#8594; evaluation.</text>')

# ---------------- region eyebrows + separators ----------------
eyebrow(30,104,"DATA PREPROCESSING",DATA)
eyebrow(560,104,"STAGE 1 · DISTRIBUTION LEARNING",S1)
eyebrow(1000,104,"STAGE 2 · CONDITIONAL FINE-TUNING",S2)
eyebrow(1400,104,"EVALUATION",EVAL)
for sx in (542,972,1388):
    add(f'<line x1="{sx}" y1="118" x2="{sx}" y2="566" stroke="{BORD}" stroke-width="1" stroke-dasharray="3 5"/>')

# ---------------- training backbone (cy=226) ----------------
box(590,120,170,40,"Base LLM","Mistral-7B · Qwen3-4B",stroke=ART,tsize=13,subsize=9)
stagebox(560,170,230,112,"Plaintext Distribution","Learning","full FT · no LoRA · p(password)",S1_F,S1,"2",S1)
box(812,201,120,50,"Distribution model","final/",stroke=ART,tsize=12,subsize=9)
stagebox(1000,170,230,112,"Conditional Targeted","Fine-tuning","QLoRA · tags → password",S2_F,S2,"3",S2)
box(1252,201,118,50,"Final model","lora_final",stroke=ART,tsize=12,subsize=9)
stagebox(1400,170,150,112,"Evaluation","","crack rate @K",EVAL_F,EVAL,"4",EVAL)

arrow([(675,160),(675,170)])                      # Base -> Stage1
arrow([(790,226),(812,226)])                      # Stage1 -> Dist model
arrow([(932,226),(1000,226)],col=S2,dash=True,sw=2.2)  # Dist -> Stage2 (weight reuse)
arrow([(1230,226),(1252,226)])                    # Stage2 -> Final
arrow([(1370,226),(1400,226)])                    # Final -> Eval

# phase captions
wrap(560,306,"Full-parameter fine-tuning on ~2.74M cleaned passwords; learns the unconditional distribution p(password) via causal-LM cross-entropy.",238,size=11)
wrap(1010,306,"Initialized from the Stage-1 model. QLoRA conditions generation on PCFG tags (tags → password); loss on password tokens only.",234,size=11)
wrap(1400,306,"Targeted guessing; crack rate at K = 1 / 10 / 100 / 1000 candidates.",150,size=11)

# ---------------- data preprocessing (lower-left) ----------------
box(30,338,150,44,"Raw passwords","datasets/*.txt",center=True,tsize=13,stroke=ART,subsize=9)
box(200,338,160,44,"Clean / filter","dedup · strip-test",center=True,tsize=13,subsize=9)
box(380,336,160,48,"Plaintext corpus","≈ 2.74M rows",fill=DATA_F,stroke=DATA,sw=2,center=True,tsize=13,tcol=DATA,subsize=9)
arrow([(180,360),(200,360)]); arrow([(360,360),(380,360)])

box(30,456,150,44,"JSON data","sibling·pii·others",center=True,tsize=13,stroke=ART,subsize=9)
MX,MY,MW,MH=198,450,162,58
add(f'<rect x="{MX}" y="{MY}" width="{MW}" height="{MH}" rx="12" fill="#fbfaf7" stroke="{MODB}" stroke-width="1.6" stroke-dasharray="6 4"/>')
add(f'<rect x="{MX+8}" y="{MY-13}" width="92" height="24" rx="12" fill="{DATA}"/>')
add(f'<text x="{MX+19}" y="{MY+3}" font-family="{SANS}" font-size="11" font-weight="700" fill="#fff">module</text>')
box(MX+10,MY+20,66,32,"Split",None,center=True,tsize=12)
box(MX+88,MY+20,66,32,"Tag",None,center=True,tsize=12)
arrow([(MX+76,MY+36),(MX+88,MY+36)])
box(380,454,160,50,"Conditional data","split + PCFG tag",fill=DATA_F,stroke=DATA,sw=2,center=True,tsize=13,tcol=DATA,subsize=9)
arrow([(180,478),(MX+10,478)]); arrow([(MX+154,478),(380,478)])

# data-region caption
wrap(30,542,"Two sources. Plaintext passwords are cleaned (dedup, length/charset filter, test-overlap removal). Structured JSON (sibling / PII / other) enters a module that first segments passwords into tokens (Split) and then assigns PCFG tags (Tag).",505,size=11)

# feeds into the backbone
arrow([(540,356),(560,262)],col=DATA,sw=2)                        # plaintext corpus -> Stage1 (left)
note(500,322,"plaintext",col=DATA,size=9.5)
arrow([(540,479),(986,479),(986,256),(1000,256)],col=DATA,sw=2)   # conditional data -> Stage2 (left)
note(762,471,"conditional (tags)",col=DATA,size=9.5,anchor="middle")

# ---------------- weight-reuse legend + figure caption ----------------
add(f'<line x1="30" y1="600" x2="64" y2="600" stroke="{S2}" stroke-width="2.2" stroke-dasharray="6 4"/>')
note(72,604,"weight reuse: the Stage-1 model initializes Stage-2.",col=MUT,size=11,font=SANS)
add(f'<text x="30" y="626" font-family="{SANS}" font-size="11.5" font-style="italic" fill="{MUT}">Figure 1. Two-stage pipeline: unconditional plaintext distribution learning (Stage 1) followed by PCFG-tag-conditioned targeted fine-tuning (Stage 2).</text>')

W,H=1580,644
svg=(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
     f'<rect width="{W}" height="{H}" fill="#ffffff"/>' + "".join(el) + '</svg>')
base="/work/u4996812/tmp/claude-43574/-home-u4996812-llm-pcfg-cracking/bd00bf48-28fd-4a66-9301-c50822ea5478/scratchpad/two_stage_arch_landscape"
open(base+".svg","w").write(svg)
cairosvg.svg2png(bytestring=svg.encode(),write_to=base+".png",output_width=W*2,output_height=H*2,background_color="#ffffff")
print("wrote",base+".png")
