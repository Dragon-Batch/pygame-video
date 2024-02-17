from .exceptions import NoAudioOrVideoException
from .Vector2 import Vector2
from .Font import Font
import subprocess
import traceback
import threading
import pyaudio
import pygame
import json
import time

class Video:
    def __init__(self, source: str, font: Font = None, block: bool = False, play_audio: bool = True, audio_output_index: int = None):
        # the source of all audio/video
        self.source = source

        # the font class for drawing text when self.draw is called
        self.font = font or Font("Ariel", 24)

        # internal locks to prevent race conditions between threads
        self.frame_lock = threading.Lock()
        self.seeking_lock = threading.Lock()

        # will only be used if only self.has_video
        self.clock = pygame.time.Clock()

        # frame will a pygame.Surface or None if there is no frame
        self.frame = None

        # this will be used when self.draw is called
        self.info_surface: pygame.Surface = None

        # ffmpeg processes to get video/audio from source
        self.video_process: subprocess.Popen = None
        self.audio_process: subprocess.Popen = None

        # set parameters for audio
        self.play_audio = play_audio
        self.audio_output_index = audio_output_index

        # the output stream for source audio
        # this will only be set if source has audio and self.play_audio is True
        self.speakers: pyaudio.Stream = None

        # internal state
        self.playing = True
        self.pressed = ""
        self.progress = 0

        # metadata of the source
        self.has_audio = False
        self.has_video = False
        self.duration = -1
        self.framerate = -1
        self.video_size = Vector2(-1, -1)
        self.samplerate = -1
        self.channels = -1

        if block:
            self.setup_thread()

        else:
            threading.Thread(target = self.setup_thread, daemon = True).start()

    def start_ffmpeg_at_offset(self, start_offset: float = 0):
        if self.seeking_lock.locked(): return
        with self.seeking_lock, self.frame_lock:
            self.progress = start_offset
            if self.has_video:
                if self.video_process:
                    self.video_process.terminate()
                    self.video_process = None

                self.video_process = subprocess.Popen(
                    ["ffmpeg", "-v", "error", "-hwaccel", "auto", "-seek_timestamp", "1", "-threads", "8", "-ss", str(start_offset), "-i", self.source, "-filter:v", "setpts=PTS-STARTPTS", "-r", str(self.framerate), "-s", f"{int(self.video_size.x)}x{int(self.video_size.y)}", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],
                    stdout = subprocess.PIPE,
                    shell = False
                )

                self.frame = pygame.image.frombuffer(
                    self.video_process.stdout.read(int(self.video_size.x * self.video_size.y * 3)),
                    (int(self.video_size.x), int(self.video_size.y)), "RGB"
                )

            if self.has_audio and self.play_audio:
                if self.audio_process:
                    self.audio_process.terminate()
                    self.audio_process = None

                if self.speakers:
                    self.speakers.close()
                    self.speakers = None

                self.speakers = pyaudio.PyAudio().open(self.samplerate, self.channels, pyaudio.paInt16, output = True)
                self.audio_process = subprocess.Popen(
                    ["ffmpeg", "-v", "error", "-hwaccel", "auto", "-seek_timestamp", "1", "-threads", "8", "-ss", str(start_offset), "-i", self.source, "-itsoffset", str(round(self.speakers.get_output_latency(), 2)), "-i", self.source, "-r", str(self.framerate), "-filter:a", "asetpts=PTS-STARTPTS", "-f", "s16le", "-ar", str(self.samplerate), "-ac", str(self.channels), "pipe:1"],
                    stdout = subprocess.PIPE, shell = False
                )

                if self.has_audio:
                    self.audio_process.stdout.read(self.calculate_pcm_bytes_to_read(
                        0.1 if not self.has_video else (1 / self.framerate), self.channels, self.samplerate
                    ))

    def setup_thread(self):
        self.extract_metadata()
        self.start_ffmpeg_at_offset(0)

        # _internal_player_thread cant be created until extract_metadata if executed
        # otherwise it will just return because has_video and has_audio are set to False by default
        threading.Thread(target = self._internal_player_thread, daemon = True).start()      

    def extract_metadata(self):
        metadata: dict[str, str] = json.loads(subprocess.run(
            ["ffprobe", "-v", "error", "-show_streams", "-print_format", "json", '-show_entries', 'format=duration', self.source],
            capture_output = True, shell = False, text = True
        ).stdout)

        with self.seeking_lock, self.frame_lock:
            self.duration: float = float(metadata["format"]["duration"])
            for stream in metadata['streams']:
                print(stream)
                if stream['codec_type'] == 'video':
                    self.video_size = Vector2(stream['width'], stream['height'])
                    parts = [float(p) for p in stream["r_frame_rate"].split("/")]
                    self.framerate = int(abs(parts[0] / parts[1]) + 1)
                    self.has_video = True

                if stream['codec_type'] == 'audio' and self.play_audio:
                    self.samplerate = int(stream["sample_rate"])
                    self.channels = stream["channels"]
                    self.has_audio = True

        if self.has_audio and self.play_audio:
            self.speakers = pyaudio.PyAudio().open(self.samplerate, self.channels, pyaudio.paInt16, output = True, output_device_index = self.audio_output_index)

    def calculate_pcm_bytes_to_read(self, t: float, channels: int, samplerate: int):
        return int(samplerate * t) * channels * 2

    def _internal_player_thread(self):
        while True:
            if not self.playing:
                time.sleep(0.1)
                continue

            # if there is no audio or video to be played then end this loop
            if not self.has_audio and not self.has_video:
                return

            # wait for the video process to be spawned
            if self.has_video and not self.video_process:
                self.clock.tick(self.framerate)
                continue

            # wait for the audio process to be spawned
            if self.has_audio and not self.audio_process:
                time.sleep(0.1)

            # wait for the audio output to be opened
            if self.has_audio and not self.speakers:
                time.sleep(0.1)

            if self.progress >= self.duration:
                time.sleep(0.1)
                continue

            # if the source does not have audio then we will wait the framerate
            if self.has_video and not self.has_audio:
                self.clock.tick(self.framerate)

            with self.frame_lock:
                frame_data = b''
                audio_data = b''

                try:
                    if self.has_video:
                        frame_data = self.video_process.stdout.read(int(self.video_size.x * self.video_size.y * 3))
                        if frame_data:
                            self.frame = pygame.image.frombuffer(
                                frame_data, (int(self.video_size.x), int(self.video_size.y)), "RGB"
                            )

                    if self.has_audio and self.play_audio:
                        audio_data = self.audio_process.stdout.read(self.calculate_pcm_bytes_to_read(
                            0.1 if not self.has_video else (1 / self.framerate), self.channels, self.samplerate
                        ))

                        if audio_data:
                            self.speakers.write(audio_data)

                    if not frame_data and not audio_data:
                        raise NoAudioOrVideoException

                    self.progress += 0.1 if not self.has_video else 1 / self.framerate

                except NoAudioOrVideoException:
                    if not self.progress >= self.duration:
                        self.progress += 0.1 if not self.has_video else 1 / self.framerate

                    else: print("end of video")

                except Exception as error:
                    traceback.print_exception(error)

    def fit_resolution(self, from_res, to_res):
        width1, height1 = from_res
        width2, height2 = to_res

        # Calculate aspect ratios
        aspect_ratio1 = width1 / height1
        aspect_ratio2 = width2 / height2

        # Calculate the new width and height for from_res to fit inside to_res
        if aspect_ratio1 > aspect_ratio2:
            new_width1 = width2
            new_height1 = int(width2 / aspect_ratio1)
        else:
            new_height1 = height2
            new_width1 = int(height2 * aspect_ratio1)

        return new_width1, new_height1

    def calculate_elapsed_rect(self, area: pygame.Rect, height: int = 18) -> pygame.Rect:
        elapsed_rect = pygame.Rect(0, 0, 60, height)
        elapsed_rect.bottom = area.bottom - 5
        elapsed_rect.left = area.left + 5
        return elapsed_rect

    def calculate_remainder_rect(self, area: pygame.Rect, height: int = 18) -> pygame.Rect:
        remainder_rect = pygame.Rect(0, 0, 60, height)
        remainder_rect.bottom = area.bottom - 5
        remainder_rect.right = area.right - 5
        return remainder_rect

    def calculate_seekbar_rect(self, area: pygame.Rect, height: int = 18) -> pygame.Rect:
        seekbar_rect = pygame.Rect(0, 0, area.width - 140, height)
        seekbar_rect.bottom = area.bottom - 5
        seekbar_rect.centerx = area.centerx
        return seekbar_rect

    def get_frame(self, size: tuple[int, int]):
        frame = self.frame
        if frame:
            return pygame.transform.smoothscale(frame, self.fit_resolution(frame.get_size(), size))
        return False

    def generate_timestamp(self, duration: float):
        hours = int(duration / (60 * 60))
        minutes = int(duration / 60)
        seconds = int(duration % 60)

        timestamp = ""
        if hours != 0:
            timestamp += ("0" * (2 - len(str(hours)))) + str(hours) + ":"

        # if minutes != 0:
        timestamp += ("0" * (2 - len(str(minutes)))) + str(minutes) + ":"
        timestamp += ("0" * (2 - len(str(seconds)))) + str(seconds)

        return timestamp

    def mouse_down(self, area: pygame.Rect, mouse_pos: Vector2):
        height = 28
        seekbar_rect = self.calculate_seekbar_rect(area, height)

        if mouse_pos.x > seekbar_rect.left and mouse_pos.x < seekbar_rect.right and mouse_pos.y > seekbar_rect.top and mouse_pos.y < seekbar_rect.bottom:
            self.pressed = "progress_bar"

            pos = (mouse_pos.x - seekbar_rect.left)
            pos = max(0, min(seekbar_rect.width, pos))
            progress = self.duration * (pos / seekbar_rect.width)
            print(progress)
            if not self.seeking_lock.locked():
                threading.Thread(target = lambda: self.start_ffmpeg_at_offset(int(progress))).start()

        else:
            self.pressed = ""

    def mouse_move(self, area: pygame.Rect, mouse_pos: Vector2):
        height = 28
        seekbar_rect = self.calculate_seekbar_rect(area, height)

        if self.pressed == "progress_bar":
            pos = (mouse_pos.x - seekbar_rect.left)
            pos = max(0, min(seekbar_rect.width, pos))
            progress = self.duration * (pos / seekbar_rect.width)
            if not self.seeking_lock.locked():
                threading.Thread(target = lambda: self.start_ffmpeg_at_offset(int(progress))).start()

    def mouse_up(self, area: pygame.Rect, mouse_pos: Vector2):
        self.pressed = ""

    def draw(self, display: pygame.Surface, area: pygame.Rect):
        frame = self.get_frame(area.size)
        if frame:
            display.blit(frame, frame.get_rect(center = area.center))

        else:
            display.fill((0, 0, 0), area)


        height = 28
        remainder_rect = self.calculate_remainder_rect(area, height)
        seekbar_rect = self.calculate_seekbar_rect(area, height)
        elapsed_rect = self.calculate_elapsed_rect(area, height)

        info_surface = self.info_surface
        if not info_surface:
            info_surface = pygame.Surface((area.w, height)).convert_alpha()
            self.info_surface = info_surface
            info_surface.set_alpha(127)

        elif not info_surface.get_size() == (int(area.w), height):
            info_surface = pygame.Surface((area.w, height)).convert_alpha()
            self.info_surface = info_surface
            info_surface.set_alpha(127)

        info_surface.fill((0, 0, 0, 0))

        elapsed_rect.top = 0
        seekbar_rect.top = 0
        remainder_rect.top = 0

        pygame.draw.rect(info_surface, (55, 55, 55, 255), elapsed_rect)
        pygame.draw.rect(info_surface, (55, 55, 55, 255), seekbar_rect)
        pygame.draw.rect(info_surface, (55, 55, 55, 255), remainder_rect)

        seekbar_rect.w = (self.progress / self.duration) * seekbar_rect.w
        pygame.draw.rect(info_surface, (88, 88, 88, 255), seekbar_rect)

        elapsed_text, _ = self.font.render_max_width(self.generate_timestamp(int(self.progress)), elapsed_rect.w)
        info_surface.blit(elapsed_text, elapsed_text.get_rect(center = elapsed_rect.center))

        elapsed_text, _ = self.font.render_max_width(self.generate_timestamp(int(self.duration - self.progress)), remainder_rect.w)
        info_surface.blit(elapsed_text, elapsed_text.get_rect(center = remainder_rect.center))

        display.blit(info_surface, (0, area.bottom - height - 5))