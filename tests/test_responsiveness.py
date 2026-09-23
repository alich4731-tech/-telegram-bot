"""No live Telegram/OpenAI calls; reproduce a slow AI request."""
import asyncio
import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from telegram.ext import Application

with patch.dict(os.environ, {
    'BOT_TOKEN': '123456:local-test-token',
    'OPENAI_API_KEY': '',
    'RENDER_EXTERNAL_URL': 'https://example.invalid',
}), patch.object(Application, 'run_webhook'):
    spec = importlib.util.spec_from_file_location('bot_under_test', Path(__file__).parents[1] / 'bot.py')
    bot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bot)


class ResponsivenessTests(unittest.IsolatedAsyncioTestCase):
    async def test_start_replies_while_ai_is_still_waiting(self):
        entered, release = asyncio.Event(), asyncio.Event()

        async def slow_response(**kwargs):
            entered.set()
            await release.wait()
            return SimpleNamespace(output_text='A complete answer.', output=[], status='completed')

        fake_client = SimpleNamespace(responses=SimpleNamespace(create=slow_response))
        ai_context = SimpleNamespace(user_data={})
        reply = AsyncMock()
        update = SimpleNamespace(message=SimpleNamespace(reply_text=reply))
        with patch.object(bot, 'client', fake_client):
            pending = asyncio.create_task(bot._request_ai([], 'Hello', ai_context))
            try:
                await asyncio.wait_for(entered.wait(), 1)
                await asyncio.wait_for(bot.start(update, SimpleNamespace(user_data={})), .2)
                reply.assert_awaited_once()
                self.assertFalse(pending.done())
            finally:
                release.set()
                answer, _ = await asyncio.wait_for(pending, 1)
            self.assertEqual(answer, 'A complete answer.')
            self.assertEqual(len(ai_context.user_data['ai_history']), 2)

    async def test_slow_profile_update_does_not_prevent_startup(self):
        cancelled = asyncio.Event()

        async def slow_description(*args):
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

        application = SimpleNamespace(bot=SimpleNamespace(set_my_description=slow_description))
        await asyncio.wait_for(bot.post_init(application), 3.5)
        self.assertTrue(cancelled.is_set())

    async def test_shutdown_closes_ai_client(self):
        client = SimpleNamespace(close=AsyncMock())
        with patch.object(bot, 'client', client):
            await bot.post_shutdown(None)
        client.close.assert_awaited_once()


if __name__ == '__main__':
    unittest.main()
