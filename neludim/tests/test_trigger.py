
from neludim.trigger import build_app


PAYLOAD = {
    'messages': [
	{
	    'event_metadata': {
		'event_type': 'yandex.cloud.events.serverless.triggers.TimerMessage',
		'created_at': '2022-08-31T09:31:10.869181208Z',  # wednesday
		'folder_id': 'b1gvn9housafmd323832'
	    },
	    'trigger_id': 'a1s8tlitsoh648k1sun5'
	}
    ]
}


async def test_trigger(aiohttp_client, context):
    app = build_app(context)
    client = await aiohttp_client(app)
    await client.post('/', json=PAYLOAD)
