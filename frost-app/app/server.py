from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import uvicorn, aiohttp, asyncio
from io import BytesIO

from fastai import *
from fastai.vision import *

model_file_url = 'https://drive.google.com/uc?export=download&id=1RjgBFNqBsj1Vl58TUj2bjxLvMQbvcoK-'
#'https://drive.google.com/uc?export=download&confirm=vkxu&id=1bVyrogP_SlLk8MAzm4H3epVGQ1oV2Xdg'
model_file_name = 'export.pkl'
classes = ['frost','husky']
path = Path(__file__).parent

app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))

async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f: f.write(data)

async def setup_learner():
    await download_file(model_file_url, path/'models'/model_file_name)
    # data_bunch = ImageDataBunch.single_from_classes(path, classes,
    #     ds_tfms=get_transforms(), size=256).normalize(imagenet_stats)
    # learn = cnn_learner(data_bunch, models.resnet34, pretrained=False)
    # learn.load(model_file_name)
    learn = load_learner(path / 'models')
    return learn

loop = asyncio.get_event_loop()
tasks = [asyncio.ensure_future(setup_learner())]
learn = loop.run_until_complete(asyncio.gather(*tasks))[0]
loop.close()

@app.route('/')
def index(request):
    html = path/'view'/'index.html'
    return HTMLResponse(html.open().read())

@app.route('/analyze', methods=['POST'])
async def analyze(request):
    data = await request.form()
    img_bytes = await (data['file'].read())
    img = open_image(BytesIO(img_bytes))
    return JSONResponse({'result': str(learn.predict(img)[0])})


if __name__ == '__main__':
    if 'serve' in sys.argv: uvicorn.run(app, host='0.0.0.0', port=8080)

