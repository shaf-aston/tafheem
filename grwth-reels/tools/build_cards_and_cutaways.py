import json,subprocess,shutil,os
B='/tmp/claude-0/-home-user-tafheem/8da1ac7c-cc1d-5ff9-b059-1539c9419264/scratchpad/grwth'
def C(name,at,ln,spec): return ('mg',name,at,ln,spec)
def R(src,frm,at,ln): return ('br',src,at,ln,frm)
P={
'close-anywhere':('2026-11-16-close-anywhere-v3.mp4',0.6,[
 R('desk0054',0.4,3.9,1.0),
 C('ca1',5.4,1.4,'ANYWHERE@0|AND@0.35|EVERYWHERE@0.7:ice'),
 R('lap0088',2.0,8.6,1.3),
 C('ca2',10.6,0.9,'THE RIGHT@0|SKILLS@0.25:ice:big'),
 C('ca3',12.0,1.0,'SILLY@0|COACHES@0.2:ice'),
 C('ca4',14.2,0.9,'SO MUCH@0|MORE@0.3:ice:big'),
 C('ca5',16.0,1.0,'ACTUALLY@0|CLOSE@0.3:ice:big'),
 C('ca6',18.95,1.27,'SIMPLE.@0:ice:big')]),
'25k-not-salesy':('2026-11-16-25k-not-salesy-v3.mp4',0.63,[
 C('k1',3.05,2.0,'SALES@0|RESISTANCE@0.15:ice|OBJECTIONS@1.05'),
 R('stg0363',2.5,7.0,1.3),
 R('greet0038',0,9.98,1.3),
 C('k2',13.45,1.0,'NOT@0|SALESY@0.35:ice:big'),
 C('k3',14.95,2.85,'THE@0|OPPOSITE@0.15:ice:big|OF THE@0.6|COACHES@0.9:big')]),
'time-over-money':('2026-11-16-time-over-money-v2.mp4',0.55,[
 C('t1',5.65,3.05,'FANCY CARS@0|LAMBORGHINIS@1.1:ice|FERRARIS@2.0:ice'),
 C('t2',11.25,1.0,'HIGH-TICKET@0|SALES@0.3:ice:big'),
 R('drive0058',0,12.96,1.3),
 C('t3',14.4,0.9,'YOUR@0|TIME@0.15:ice:big'),
 C('t4',16.55,1.0,'FRIDAY@0|AFTERNOON@0.3:ice'),
 R('cafe0300',0,18.56,1.89)]),
'ihsan-excellence':('2026-11-16-ihsan-excellence-v4.mp4',0.55,[
 R('aud0378',14.0,5.0,1.3),
 C('i1',7.4,0.9,'EXCELLENCE@0:ice:big'),
 R('room0034',0,9.68,1.3),
 C('i2',11.2,1.4,'PAY FOR@0|TALENT@0.9:ice:big'),
 C('i3',13.5,1.3,'NO CUTTING@0|CORNERS@0.6:ice:big'),
 C('i4',17.4,0.8,'MEDIOCRITY@0:ice'),
 C('i5',21.35,2.25,'THE 1%@0:big|THE@0.5|EXCEPTION@1.0:ice:big')]),
'last-dollar':('2026-11-16-last-dollar-v4.mp4',0.55,[
 C('l1',6.55,0.9,'CONDITIONED@0:ice'),
 C('l2',8.95,1.1,'THE SALES@0|MATRIX@0.2:ice:big'),
 R('call0083',0,11.58,1.3),
 C('l3',15.7,0.75,'NOT@0|NECESSARILY@0.1|TRUE.@0.4:ice:big'),
 C('l4',18.35,0.8,'GURUS@0:ice:big'),
 C('l5',20.35,1.0,"EVERYBODY'S@0|LAST@0.35|DOLLAR@0.5:ice:big"),
 C('l6',22.05,1.55,'THE MINDSET@0|THAT SERVES@0.3|YOU@0.5:ice:big')]),
}
for r,(out,tail,items) in P.items():
    d=f'{B}/reels/{r}'; cfg=json.load(open(f'{d}/reel.json'))
    if not os.path.exists(f'{d}/reel_v2_backup.py'): shutil.copy(f'{d}/reel_local.py',f'{d}/reel_v2_backup.py')
    shutil.copy(f'{B}/reels/pure-intent/reel_local.py',f'{d}/reel_local.py')
    for k in ('cap_y','cap_y_from','end_card'): cfg.pop(k,None)
    cfg['out']=out; cfg['tail']=tail; cfg['hook_shade']=True; cuts=[]; nc=[]
    for it in items:
        if it[0]=='mg':
            _,n,at,ln,spec=it; subprocess.run(['python3',f'{B}/tools/mg.py',f'{B}/mg/{n}.mp4',str(ln+0.1),spec],check=True)
            cuts.append({'src':f'../../mg/{n}.mp4','from':0,'len':ln,'at':at,'y':0.5}); nc.append([round(at-0.05,2),round(at+ln+0.05,2) if at+ln<30 else 30])
        else:
            _,s,at,ln,frm=it; cuts.append({'src':f'../../src/{s}.mp4','from':frm,'len':ln,'at':at,'y':0.5})
    if nc and items[-1][0]=='mg': nc[-1][1]=30
    cfg['cutaways']=cuts; cfg['no_caps']=nc
    json.dump(cfg,open(f'{d}/reel.json','w'),indent=1)
    subprocess.run(['python3','reel_local.py','cut','reel.json'],cwd=d,check=True)
    subprocess.run(['python3','reel_local.py','render','reel.json'],cwd=d,check=True)
