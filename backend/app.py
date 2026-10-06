"""Render local uploads with FFmpeg. No user text is interpolated into a shell."""
import json
import os
import subprocess
import threading
import shutil
from pathlib import Path
from uuid import uuid4
import imageio_ffmpeg
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from .web import serve_web

app = FastAPI(title='Framecraft')
ROOT = Path(os.environ.get('DEMO_DATA',Path(__file__).resolve().parents[1]/'data'))
ROOT.mkdir(parents=True,exist_ok=True)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
JOBS = {}
LOCK = threading.Lock()
RENDER_LOCK = threading.Lock()
MAX_BYTES = 50*1024*1024

def command(args, timeout=90):
    done = subprocess.run([FFMPEG,'-hide_banner','-y',*args],capture_output=True,timeout=timeout,
                          creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    if done.returncode: raise ValueError('FFmpeg не смог обработать этот файл')
    return done

def sample():
    output = ROOT/'sample.mp4'
    with LOCK:
        if not output.exists():
            bundled = Path(__file__).resolve().parents[1]/'dist'/'sample.mp4'
            if bundled.exists():
                shutil.copyfile(bundled,output)
                return output
            command(['-f','lavfi','-i','color=c=0x21344c:s=540x960:r=24:d=8',
                     '-f','lavfi','-i','sine=frequency=220:duration=8',
                     '-vf',"drawgrid=w=100:h=100:t=1:c=0xfffcf5@0.12,drawbox=x='150+t*30':y=160:w=260:h=400:color=0xe5ddc5:t=fill,drawbox=x=700:y=220:w=320:h=280:color=0xa9be94:t=fill",
                     '-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(output)])
    return output

class Edit(BaseModel):
    source: str = 'sample'
    start: float = Field(default=0,ge=0,le=290)
    duration: float = Field(default=5,ge=1,le=30)
    caption: str = Field(default='Новая коллекция',max_length=200)
    style: str = 'forest'

def render(job, edit):
    try:
        source = sample() if edit.source=='sample' else ROOT/(edit.source+'.media')
        if not source.exists(): raise ValueError('Исходное видео не найдено')
        import av
        with av.open(str(source)) as media:
            if not media.streams.video: raise ValueError('В файле нет видеодорожки')
            seconds = (media.duration or 0)/1_000_000
            if seconds and edit.start+edit.duration > seconds+0.1:
                raise ValueError(f'Конец фрагмента выходит за длину видео ({seconds:.1f} с)')
        folder = ROOT/job
        folder.mkdir()
        # Fixed text file avoids filter injection; paths escaped for FFmpeg's filter parser.
        caption = folder/'caption.txt'
        caption.write_text(edit.caption,encoding='utf-8')
        font = Path('C:/Windows/Fonts/arial.ttf') if os.name=='nt' else Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
        if font.exists(): shutil.copy(font,folder/'font.ttf')
        font_option = 'fontfile=font.ttf:' if font.exists() else ''
        tone = '0x315943' if edit.style=='forest' else '0x293447'
        filters = (f'scale=540:960:force_original_aspect_ratio=increase,crop=540:960,setsar=1,'
                   f'drawbox=x=0:y=760:w=iw:h=200:color={tone}@0.94:t=fill,'
                   f"drawtext={font_option}textfile=caption.txt:fontcolor=0xfffcf5:fontsize=26:x=32:y=820")
        output = folder/'film.mp4'
        args = [FFMPEG,'-hide_banner','-y','-ss',str(edit.start),'-i',str(source),'-t',str(edit.duration),
                '-vf',filters,'-c:v','libx264','-preset','veryfast','-crf','22','-c:a','aac','-pix_fmt','yuv420p',
                '-movflags','+faststart','-progress','pipe:1','-nostats',str(output)]
        JOBS[job]['state']='rendering'
        log = (folder/'ffmpeg.log').open('w',encoding='utf-8')
        process = subprocess.Popen(args,stdout=subprocess.PIPE,stderr=log,text=True,cwd=folder,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        try:
            # A watchdog bounds malformed/hostile local uploads, even if progress stops.
            timer = threading.Timer(90,process.kill)
            timer.start()
            for line in process.stdout:
                if line.startswith('out_time_us='):
                    try: JOBS[job]['progress']=min(99,int(int(line.split('=')[1])/1e6/edit.duration*100))
                    except ValueError: pass
            if process.wait()!=0 or not output.exists(): raise ValueError('Рендер не завершился; попробуйте другое видео')
        finally: timer.cancel();log.close()
        JOBS[job].update(state='completed',progress=100,url=f'/api/renders/{job}/file',bytes=output.stat().st_size)
    except Exception as error:
        JOBS[job].update(state='failed',error=str(error) if isinstance(error,ValueError) else 'Не удалось обработать файл')
    finally: RENDER_LOCK.release()

@app.get('/api/sample')
def demo_video(): return FileResponse(sample(),media_type='video/mp4')

@app.post('/api/uploads')
async def upload(file:UploadFile=File(...)):
    fid=uuid4().hex
    target=ROOT/(fid+'.media')
    size=0
    try:
        with target.open('wb') as stream:
            while chunk:=await file.read(1024*1024):
                size+=len(chunk)
                if size>MAX_BYTES: raise HTTPException(413,'Максимум 50 МБ')
                stream.write(chunk)
        import av
        with av.open(str(target)) as media:
            if not media.streams.video or (media.duration or 0)>300_000_000:
                raise ValueError()
            seconds=(media.duration or 0)/1e6
    except HTTPException:
        target.unlink(missing_ok=True); raise
    except Exception:
        target.unlink(missing_ok=True); raise HTTPException(422,'Нужно видео длительностью до 5 минут')
    return {'id':fid,'duration':seconds,'url':f'/api/uploads/{fid}'}

@app.get('/api/uploads/{fid}')
def source_file(fid:str):
    if len(fid)!=32 or not all(c in '0123456789abcdef' for c in fid): raise HTTPException(404)
    target=ROOT/(fid+'.media')
    if not target.exists(): raise HTTPException(404)
    return FileResponse(target,media_type='video/mp4')

@app.post('/api/renders')
def start(edit:Edit):
    if edit.source!='sample' and (len(edit.source)!=32 or not all(c in '0123456789abcdef' for c in edit.source)):
        raise HTTPException(422,'Неверный идентификатор видео')
    if edit.style not in {'forest','night'}: raise HTTPException(422,'Выберите стиль forest или night')
    if not RENDER_LOCK.acquire(blocking=False): raise HTTPException(429,'Рендер занят. Дождитесь окончания.')
    job=uuid4().hex
    JOBS[job]={'id':job,'state':'queued','progress':0}
    threading.Thread(target=render,args=(job,edit),daemon=True).start()
    return JOBS[job]

@app.get('/api/renders/{job}')
def status(job:str):
    if job not in JOBS: raise HTTPException(404)
    return JOBS[job]

@app.get('/api/renders/{job}/file')
def film(job:str):
    if job not in JOBS or JOBS[job]['state']!='completed': raise HTTPException(404)
    return FileResponse(ROOT/job/'film.mp4',media_type='video/mp4',filename='framecraft.mp4')

@app.get('/api/health')
def health(): return {'status':'ok'}
serve_web(app)
