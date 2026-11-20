#!/usr/bin/env python3
# Paper-style (dashed panels + gray headers + pastel boxes + hollow block arrows) figure. Local only.
import cairosvg, math
SANS="DejaVu Sans, sans-serif"; MONO="DejaVu Sans Mono, monospace"
DK="#1f2328"; MUT="#555b61"
BLUE="#dde3fb"; RED="#fbdada"; GRN="#d5efd5"; WHT="#ffffff"
HDR="#ededed"; PANEL="#5a5f66"
el=[]; add=el.append

def panel(x,y,w,h,title):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="none" stroke="{PANEL}" stroke-width="1.6" stroke-dasharray="7 5"/>')
    add(f'<rect x="{x+10}" y="{y+10}" width="{w-20}" height="30" rx="6" fill="{HDR}" stroke="{DK}" stroke-width="1"/>')
    add(f'<text x="{x+w/2}" y="{y+30}" font-family="{SANS}" font-size="15" font-weight="700" fill="{DK}" text-anchor="middle">{title}</text>')

def pbox(x,y,w,h,title,sub=None,fill=WHT,tsize=12.5,subsize=9,rx=6):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{DK}" stroke-width="1.3"/>')
    cx=x+w/2
    if sub:
        add(f'<text x="{cx}" y="{y+h/2-1}" font-family="{SANS}" font-size="{tsize}" font-weight="700" fill="{DK}" text-anchor="middle">{title}</text>')
        add(f'<text x="{cx}" y="{y+h/2+14}" font-family="{MONO}" font-size="{subsize}" fill="{MUT}" text-anchor="middle">{sub}</text>')
    else:
        add(f'<text x="{cx}" y="{y+h/2+4.5}" font-family="{SANS}" font-size="{tsize}" font-weight="700" fill="{DK}" text-anchor="middle">{title}</text>')

def card(x,y,w,h,fill=GRN):
    add(f'<rect x="{x+5}" y="{y+5}" width="{w}" height="{h}" rx="4" fill="{fill}" stroke="{DK}" stroke-width="1.1"/>')
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}" stroke="{DK}" stroke-width="1.1"/>')

def ahead(x2,y2,ux,uy,col=DK,size=7):
    px,py=-uy,ux; bx,by=x2-ux*size,y2-uy*size
    p1=(bx+px*size*0.6,by+py*size*0.6); p2=(bx-px*size*0.6,by-py*size*0.6)
    add(f'<path d="M{x2:.1f} {y2:.1f} L{p1[0]:.1f} {p1[1]:.1f} L{p2[0]:.1f} {p2[1]:.1f} Z" fill="{col}"/>')
def arr(pts,col=DK,sw=1.5,dash=False):
    d="M"+" L".join(f"{a:.1f} {b:.1f}" for a,b in pts)
    da=' stroke-dasharray="5 4"' if dash else ''
    add(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{sw}"{da}/>')
    (x1,y1),(x2,y2)=pts[-2],pts[-1]; L=math.hypot(x2-x1,y2-y1) or 1
    ahead(x2,y2,(x2-x1)/L,(y2-y1)/L,col)

def block(xl,cy,L=46,col=DK):
    hl=22; sh=12; hh=24
    p=[(xl,cy-sh),(xl+L-hl,cy-sh),(xl+L-hl,cy-hh),(xl+L,cy),(xl+L-hl,cy+hh),(xl+L-hl,cy+sh),(xl,cy+sh)]
    d="M"+" L".join(f"{a} {b}" for a,b in p)+" Z"
    add(f'<path d="{d}" fill="#ffffff" stroke="{col}" stroke-width="1.6"/>')

def note(x,y,t,col=MUT,size=9.5,anchor="middle",font=MONO):
    add(f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" fill="{col}" text-anchor="{anchor}">{t}</text>')

# master title
add(f'<text x="24" y="40" font-family="{SANS}" font-size="21" font-weight="700" fill="{DK}">Two-Stage Password-Generation Training</text>')

PY,PH=70,410
# ---------- Panel A : Data preprocessing ----------
panel(24,PY,396,PH,"Data preprocessing")
pbox(44,128,152,46,"Raw passwords","datasets/*.txt",fill=RED)
pbox(250,128,152,46,"JSON data","sibling/pii/other",fill=RED)
pbox(44,206,152,46,"Clean / filter","dedup + strip-test")
# module
add(f'<rect x="248" y="200" width="156" height="96" rx="8" fill="#fbfaf7" stroke="{PANEL}" stroke-width="1.4" stroke-dasharray="6 4"/>')
add(f'<rect x="254" y="189" width="64" height="20" rx="10" fill="{PANEL}"/>')
add(f'<text x="286" y="203" font-family="{SANS}" font-size="10.5" font-weight="700" fill="#fff" text-anchor="middle">module</text>')
pbox(260,214,132,30,"Split",fill=WHT,tsize=11)
pbox(260,252,132,30,"Tag",fill=WHT,tsize=11)
pbox(44,322,152,50,"Plaintext corpus","~2.74M rows",fill=GRN)
pbox(250,322,152,50,"Conditional data","split + PCFG tag",fill=GRN)
arr([(120,174),(120,206)]); arr([(120,252),(120,322)])
arr([(326,174),(326,200)]); arr([(326,244),(326,252)]); arr([(326,296),(326,322)])
note(120,120,"plaintext path",col=MUT,size=9,font=SANS)
note(326,120,"JSON path",col=MUT,size=9,font=SANS)

block(424,275)

# ---------- Panel B : Stage 1 ----------
panel(470,PY,350,PH,"Stage 1 : Distribution learning")
pbox(492,126,150,44,"Plaintext corpus","~2.74M rows",fill=GRN,subsize=8.5)
pbox(650,126,150,44,"Base LLM","Mistral-7B / Qwen3-4B",fill=BLUE,subsize=8)
pbox(560,214,180,50,"Full fine-tuning","all params . no LoRA . MLE",fill=WHT,subsize=8.5)
arr([(567,170),(610,214)]); arr([(725,170),(690,214)])
note(650,296,"learn  p(password) = ∏ P(c_i | c_1..c_{i-1})",col=DK,size=10,font=SANS)
pbox(560,320,180,50,"Distribution model","stage-1 weights . final/",fill=RED,subsize=8.5)
arr([(650,264),(650,320)])

block(822,275)

# ---------- Panel C : Stage 2 (LoRA) ----------
panel(870,PY,434,PH,"Stage 2 : Conditional fine-tuning (LoRA)")
pbox(892,122,180,42,"Distribution model","init weights (frozen)",fill=RED,subsize=8)
pbox(1104,122,178,42,"Conditional data","tags → password",fill=GRN,subsize=8.5)
# LoRA mechanism
pbox(905,206,150,74,"Pre-trained  W","W : d×d  (frozen)",fill=RED,subsize=8.5)
pbox(1130,200,120,34,"B : r×d",fill=GRN,tsize=11)
pbox(1130,250,120,34,"A : d×r",fill=GRN,tsize=11)
note(1258,240,"r ≪ d",col=DK,size=10,font=SANS,anchor="start")
arr([(1190,234),(1190,250)])                       # B -> A
# plus circle
add(f'<circle cx="1070" cy="330" r="15" fill="#fff" stroke="{DK}" stroke-width="1.4"/>')
add(f'<text x="1070" y="335" font-family="{SANS}" font-size="16" fill="{DK}" text-anchor="middle">+</text>')
arr([(980,280),(1055,322)])                        # W -> +
arr([(1190,284),(1085,324)])                       # A -> +
arr([(980,164),(980,206)])                         # Dist model -> W
arr([(1190,164),(1190,200)])                       # Conditional -> B
pbox(985,358,200,46,"Final model","lora_final + adapter",fill=RED,subsize=8.5)
arr([(1070,345),(1070,358)])                       # + -> Final model
note(1085,424,"QLoRA . loss on password tokens only",col=MUT,size=9,font=SANS,anchor="middle")

block(1306,275)

# ---------- Panel D : Evaluation ----------
panel(1352,PY,384,PH,"Evaluation")
pbox(1378,128,148,42,"Input prompt","tags",fill=BLUE,subsize=8.5)
pbox(1560,128,150,42,"Trained LLM",fill=RED)
arr([(1526,149),(1560,149)])
arr([(1635,170),(1635,214)]); note(1668,196,"generate",col=MUT,size=9,font=SANS,anchor="start")
for i,xx in enumerate((1392,1470,1548,1626)):
    card(xx,218,56,44,fill=GRN)
note(1544,290,"password candidates",col=DK,size=10,font=SANS)
arr([(1544,300),(1544,330)])
pbox(1410,330,270,48,"crack rate @ K","K = 1 / 10 / 100 / 1000",fill=WHT,subsize=9)

# figure caption
add(f'<text x="24" y="512" font-family="{SANS}" font-size="12" font-style="italic" fill="{MUT}">Figure 1. Two-stage pipeline: plaintext passwords train unconditional distribution learning (Stage 1); its weights initialise a PCFG-tag-conditioned LoRA fine-tuning (Stage 2); the trained model is then evaluated by targeted guessing.</text>')

W,H=1760,536
svg=(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
     f'<rect width="{W}" height="{H}" fill="#ffffff"/>' + "".join(el) + '</svg>')
base="/work/u4996812/tmp/claude-43574/-home-u4996812-llm-pcfg-cracking/bd00bf48-28fd-4a66-9301-c50822ea5478/scratchpad/two_stage_arch_paper"
open(base+".svg","w").write(svg)
cairosvg.svg2png(bytestring=svg.encode(),write_to=base+".png",output_width=W*2,output_height=H*2,background_color="#ffffff")
print("wrote",base+".png")
