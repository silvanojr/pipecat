import aiohttp
import os
import sys

from pipecat.frames.frames import EndFrame, LLMMessagesFrame, TextFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.serializers.modaudiofork import ModAudioForkFrameSerializer
from pipecat.processors.aggregators.llm_response import (
    LLMAssistantContextAggregator,
    LLMUserContextAggregator,
)
from pipecat.services.openai import OpenAILLMContext, OpenAILLMService
from pipecat.services.deepgram import DeepgramSTTService
from pipecat.services.elevenlabs import ElevenLabsTTSService
from pipecat.transports.network.fastapi_websocket import FastAPIWebsocketTransport, FastAPIWebsocketParams
from pipecat.vad.silero import SileroVADAnalyzer

from openai.types.chat import ChatCompletionToolParam

from loguru import logger
from datetime import datetime

from dotenv import load_dotenv
load_dotenv(override=True)

logger.remove(0)
logger.add(sys.stderr, level="DEBUG")

async def start_end_call(llm):
    return None

async def end_call(llm, args):
    return {"message": "Ended"}

async def start_what_time(llm):
    await llm.push_frame(TextFrame("Checking"))

async def what_time(llm, args):
    now = datetime.now()
    return {"time": now.strftime("%I:%M %p")}

async def run_bot(websocket_client):
    async with aiohttp.ClientSession() as session:
        transport = FastAPIWebsocketTransport(
            websocket=websocket_client,
            params=FastAPIWebsocketParams(
                serializer=ModAudioForkFrameSerializer(),
                audio_in_enabled=True,
                audio_out_enabled=True,
                add_wav_header=False,
                vad_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
                vad_audio_passthrough=True
            )
        )

        llm = OpenAILLMService(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o")
        
        llm.register_function(
            "end_call",
            end_call,
            start_callback=start_end_call)
        llm.register_function(
            "what_time",
            what_time,
            start_callback=start_what_time)

        tools = [
            ChatCompletionToolParam(
                type="function",
                function={
                    "name": "end_call",
                    "description": "End the current call",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "callid": {
                                "type": "string",
                                "description": "The id of the call",
                            },
                        },
                        "required": [
                            "callid"],
                    },
                }
            ),
            ChatCompletionToolParam(
                type="function",
                function={
                    "name": "what_time",
                    "description": "Tell the current time",
                    "parameters": {},
                }
            ),
        ]

        stt = DeepgramSTTService(api_key=os.getenv('DEEPGRAM_API_KEY'))

        tts = ElevenLabsTTSService(
            aiohttp_session=session,
            api_key=os.getenv("ELEVENLABS_API_KEY"),
            voice_id=os.getenv("ELEVENLABS_VOICE_ID"),
        )

        messages = [
            {
                "role": "system",
                "content": "## Identity\nYou are Gigi, a virtual agent assisting Kooi with his phone calls. You are a pleasant and friendly executive assistant caring deeply for the caller. You don't let sales calls be transferred to your client, Kooi, but you can let personal calls be transferred.\n\n## Background for Kooi\nName: Kooi Lim\nRole: CEO of Ring By Name\nCall ID: lsjadflkjaslkdfjas\n\n## Style Guardrails\nBe Concise: Respond succinctly, addressing one topic at most.\nEmbrace Variety: Use diverse language and rephrasing to enhance clarity without repeating content.\nBe Conversational: Use everyday language, making the chat feel like talking to a friend.\nBe Proactive: Lead the conversation, often wrapping up with a question or next-step suggestion.\nAvoid multiple questions in a single response.\nGet clarity: If the user only partially answers a question, or if the answer is unclear, keep asking to get clarity.\n\n## Response Guideline\nAdapt and Guess: Try to understand transcripts that may contain transcription errors. Avoid mentioning \"transcription error\" in the response.\nStay in Character: Keep conversations within your role's scope, guiding them back creatively without repeating.\nEnsure Fluid Dialogue: Respond in a role-appropriate, direct manner to maintain a smooth conversation flow.\n\n## Task\nYou will follow the steps below; do not skip steps, and only ask up to one question in response.\n1. Begin with a self-introduction and collect information from the caller.\n  - Ask why the person is calling\n  - Ask their name\n2. Ask if they want to leave a message and store the message.\n  - When the person says bye, call function end_call",
            },
        ]

        context = OpenAILLMContext(messages, tools)
        tma_in = LLMUserContextAggregator(context)
        tma_out = LLMAssistantContextAggregator(context)

        pipeline = Pipeline([
            transport.input(),   # Websocket input from client
            stt,                 # Speech-To-Text
            tma_in,              # User responses
            llm,                 # LLM
            tts,                 # Text-To-Speech
            transport.output(),  # Websocket output to client
            tma_out              # LLM responses
        ])

        task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=True))

        @transport.event_handler("on_client_connected")
        async def on_client_connected(transport, client):
            # Kick off the conversation.
            messages.append(
                {"role": "system", "content": "Please introduce yourself to the user."})
            await task.queue_frames([LLMMessagesFrame(messages)])

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, client):
            await task.queue_frames([EndFrame()])

        runner = PipelineRunner(handle_sigint=False)

        await runner.run(task)
