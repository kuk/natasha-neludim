
from aiohttp import web


# {
#     "messages": [
# 	 {
# 	     "event_metadata": {
# 		 "event_type": "yandex.cloud.events.serverless.triggers.TimerMessage",
# 		 "created_at": "2022-08-23T10:31:10.869181208Z",
# 		 "folder_id": "b1gvn9housafmd323832"
# 	     },
# 	     "trigger_id": "a1s8tlitsoh648k1sun5"
# 	 }
#     }


async def handle_trigger(request):
    text = await request.text()
    print(text)
    return web.json_response({'status': 'ok'})


def start_webhook(context):
    app = web.Application()
    app.add_routes([
        web.post('/', handle_trigger)
    ])
    web.run_app(
        app,
        print=None
    )
