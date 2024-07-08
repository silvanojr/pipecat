#
# Copyright (c) 2024, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

from pipecat.frames.frames import AudioRawFrame, Frame
from pipecat.serializers.base_serializer import FrameSerializer

import typing
from loguru import logger


class ModAudioForkFrameSerializer(FrameSerializer):
    SERIALIZABLE_TYPES = {
        AudioRawFrame: "audio",
    }

    def __init__(self):
        self._sid = None

    def serialize(self, frame: Frame) -> str | bytes | None:
        if not isinstance(frame, AudioRawFrame):
            return None

        data = frame.audio

        if type(data).__name__ == 'bytes':
            return data
        else:
            return None

    def deserialize(self, data: str | bytes | dict) -> Frame | None:

        if "text" in data:
            text_message = typing.cast(str, data["text"])
            logger.debug(text_message)
            return None
        elif "bytes" in data:
            audio_bytes = typing.cast(bytes, data["bytes"])
            return AudioRawFrame(audio=audio_bytes, num_channels=1, sample_rate=16000)
        else:
            return None
