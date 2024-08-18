from fastapi import FastAPI, Request

app = FastAPI()

@app.get('/')
async def root():
  return {"message": "Hello"}

# b'{"action_type": "LIKE", "action_on": "POST", "action_on_id": "post_779751", "action_by": "user_6041", "action_to": "user_2979", "action_at": 1723960628688}'
@app.post('/api/like_post')
async def root(request: Request):
  body = await request.body()

@app.post('/api/like_comment')
async def root(request: Request):
  body = await request.body()

@app.post('/api/comment_post')
async def root(request: Request):
  body = await request.body()

@app.post('/api/comment_comment')
async def root(request: Request):
  body = await request.body()

@app.post('/api/send_friend_req')
async def root(request: Request):
  body = await request.body()

@app.post('/api/send_friend_req_ack')
async def root(request: Request):
  body = await request.body()

@app.post('/api/mention')
async def root(request: Request):
  body = await request.body()
