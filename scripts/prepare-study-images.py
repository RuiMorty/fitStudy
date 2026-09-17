"""Prepare reviewed transparent image assets from a JSON manifest, without generation."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',required=True);args=parser.parse_args()
    root=Path(__file__).resolve().parent.parent
    plan=json.loads(Path(args.input).read_text())
    records=[]
    for entry in plan['assets']:
        source=root/entry['source']; target=root/entry['output']
        with Image.open(source) as loaded:
            if loaded.mode!='RGBA':raise ValueError(f'Expected transparent RGBA: {source}')
            original_size=list(loaded.size); im=loaded.copy()
        alpha=im.getchannel('A')
        if alpha.getextrema()[0]!=0:raise ValueError(f'No transparent background: {source}')
        im.putalpha(alpha.point(lambda value:0 if value<=8 else value))
        crop=entry.get('crop',[0,0,im.width,im.height])
        if not (0<=crop[0]<crop[2]<=im.width and 0<=crop[1]<crop[3]<=im.height):raise ValueError('Invalid reviewed crop')
        im=im.crop(crop)
        box=im.getchannel('A').getbbox()
        if not box:raise ValueError('Empty subject')
        box=(max(0,box[0]-3),max(0,box[1]-3),min(im.width,box[2]+3),min(im.height,box[3]+3))
        width,height=entry['size'];margin=round(min(width,height)*entry.get('margin',.06))
        fitted=ImageOps.contain(im.crop(box),(width-margin*2,height-margin*2),Image.Resampling.LANCZOS)
        final=Image.new('RGBA',(width,height),(0,0,0,0))
        offset=((width-fitted.width)//2,(height-fitted.height)//2);final.alpha_composite(fitted,offset)
        target.parent.mkdir(parents=True,exist_ok=True);final.save(target)
        record={'source':entry['source'],'sourceSize':original_size,'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'reviewedCrop':crop,'visibleCrop':box,'output':entry['output'],'size':[width,height],'subjectSize':list(fitted.size),'offset':offset,'alphaRange':final.getchannel('A').getextrema(),'note':entry.get('note','')}
        records.append(record)
    output=root/plan['record']
    output.write_text(json.dumps({'processedAt':datetime.now(timezone.utc).isoformat(),'method':'trim near-transparent noise; reviewed crop; uniform scale; transparent margin','assets':records},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'prepared':len(records),'record':str(output)},ensure_ascii=False))

if __name__=='__main__':main()
