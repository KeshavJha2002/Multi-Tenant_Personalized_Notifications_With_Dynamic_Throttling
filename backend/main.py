from fastapi import FastAPI, Request, Response
from producers import producer_for_networking_topic, producer_for_comment_topic, producer_for_like_topic, producer_for_mention_topic
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
from prometheus_fastapi_instrumentator import Instrumentator


app = FastAPI()

instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app, endpoint="/metrics")

REQUEST_COUNT = Counter('api_requests_total', 'Total API requests')
REQUEST_LATENCY = Histogram('api_request_latency_seconds', 'API request latency')
@app.get('/')
async def root():
  return {"message": "Hello"}

@app.route('/metrics')
def metrics(request: Request):
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# b'{"action_type": "LIKE", "action_on": "POST", "action_on_id": "post_779751", "action_by": "user_6041", "action_to": "user_2979", "action_at": 1723960628688}'
@app.post('/api/like_post')
async def root(request: Request):
  try:
    REQUEST_COUNT.inc()
    start_time = time.time()
    body = await request.json()
    # print(body)
    await producer_for_like_topic(body)
  except Exception as e:
    return {"error": str(e)}
  finally:
    REQUEST_LATENCY.observe(time.time() - start_time)

@app.post('/api/like_comment')
async def root(request: Request):
  try:
    REQUEST_COUNT.inc()
    start_time = time.time()
    body = await request.json()
    await producer_for_like_topic(body)
  except Exception as e:
    return {"error": str(e)}
  finally:
    REQUEST_LATENCY.observe(time.time() - start_time)

@app.post('/api/comment_post')
async def root(request: Request):
    REQUEST_COUNT.inc()
    start_time = time.time()
    try:
        body = await request.json()
        await producer_for_comment_topic(body)
    except Exception as e:
        return {"error": str(e)}
    finally:
        REQUEST_LATENCY.observe(time.time() - start_time)

@app.post('/api/comment_comment')
async def root(request: Request):
  try:
    REQUEST_COUNT.inc()
    start_time = time.time()
    body = await request.json()
    await producer_for_comment_topic(body)
  except Exception as e:
    return {"error": str(e)}
  finally:
    REQUEST_LATENCY.observe(time.time() - start_time)

@app.post('/api/send_friend_req')
async def root(request: Request):
  try:
    REQUEST_COUNT.inc()
    start_time = time.time()
    body = await request.json()
    await producer_for_networking_topic(body)
  except Exception as e:
    return {"error": str(e)}
  finally:
    REQUEST_LATENCY.observe(time.time() - start_time)

@app.post('/api/send_friend_req_ack')
async def root(request: Request):
  try:
    REQUEST_COUNT.inc()
    start_time = time.time()
    body = await request.json()
    await producer_for_networking_topic(body)
  except Exception as e:
    return {"error": str(e)}
  finally:
    REQUEST_LATENCY.observe(time.time() - start_time)

@app.post('/api/mention')
async def root(request: Request):
  try:
    REQUEST_COUNT.inc()
    start_time = time.time()
    body = await request.json()
    await producer_for_mention_topic(body)
  except Exception as e:
    return {"error": str(e)}
  finally:
    REQUEST_LATENCY.observe(time.time() - start_time)
