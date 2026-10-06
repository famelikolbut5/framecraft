import time
import av
from fastapi.testclient import TestClient
from backend import app as service

client=TestClient(service.app)

def test_real_mp4_render_and_download(tmp_path,monkeypatch):
    monkeypatch.setattr(service,'ROOT',tmp_path)
    response=client.post('/api/renders',json={'duration':2,'caption':"Atelier: 50% 'quote'"})
    assert response.status_code==200
    job=response.json()['id']
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
        result=client.get('/api/renders/'+job).json()
        if result['state'] in {'completed','failed'}:break
        time.sleep(.1)
    assert result['state']=='completed',result
    media_path=tmp_path/job/'film.mp4'
    with av.open(str(media_path)) as container:
        assert container.streams.video[0].width==540
        assert container.streams.video[0].height==960
        assert 1.9<=container.duration/1e6<=2.2
        assert container.streams.audio
    download=client.get(f'/api/renders/{job}/file')
    assert download.status_code==200
    assert download.headers['content-type']=='video/mp4'
    assert len(download.content)>1000

def test_upload_garbage_and_path_traversal_rejected(tmp_path,monkeypatch):
    monkeypatch.setattr(service,'ROOT',tmp_path)
    assert client.post('/api/uploads',files={'file':('bad.mp4',b'bad','video/mp4')}).status_code==422
    assert not list(tmp_path.iterdir())
    assert client.post('/api/renders',json={'source':'../secret'}).status_code==422

def test_bad_duration_and_style():
    assert client.post('/api/renders',json={'duration':1000}).status_code==422
    assert client.post('/api/renders',json={'style':'arbitrary'}).status_code==422
