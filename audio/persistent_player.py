"""
常駐音声プレイヤーの子プロセス。

Tkinterのウィンドウとsounddeviceの音声ストリームを、
専用プロセスのメインスレッドで管理する。

親プロセスからmultiprocessing.Queue経由でWAVデータを受け取り、
音声再生と簡易レベルメーター表示を行う。
"""

import io
import queue
import wave

import numpy as np
import sounddevice as sd
import tkinter as tk
import signal

SAMPLE_RATE = 48000
CHANNELS = 2
BLOCK_SIZE = 1024
METER_BARS = 18


def run_persistent_player(
    command_queue,
    event_queue,
    app_name: str,
):
    """
    常駐音声プレイヤープロセスを実行する。
    """

    signal.signal(
        signal.SIGINT,
        signal.SIG_IGN,
    )

    player = PersistentPlayer(
        command_queue=command_queue,
        event_queue=event_queue,
        app_name=app_name,
    )

    player.run()


class PersistentPlayer:
    """
    常駐ウィンドウと音声ストリームを管理する。
    """

    def __init__(
        self,
        command_queue,
        event_queue,
        app_name: str,
    ):
        self.command_queue = command_queue
        self.event_queue = event_queue
        self.app_name = app_name

        self.root = None
        self.stream = None

        self.current_item = None
        self.current_position = 0

        self.playback_queue = queue.Queue()
        self.completed_queue = queue.Queue()

        self.level = 0.0
        self.running = True

        self.status_label = None
        self.meter = None
        self.bars = []

    def run(self):
        """
        GUIと音声ストリームを開始する。
        """
        try:
            self._create_window()
            self._start_audio_stream()

            device = sd.query_devices(
                kind="output"
            )

            self.event_queue.put({
                "type": "ready",
                "device": device["name"],
            })

            self.root.after(
                20,
                self._poll_commands,
            )

            self.root.after(
                50,
                self._update_meter,
            )

            self.root.mainloop()

        except Exception as exc:
            self.event_queue.put({
                "type": "error",
                "message": str(exc),
            })

        finally:
            self._shutdown()

    def _create_window(self):
        """
        常駐ウィンドウを作成する。
        """
        self.root = tk.Tk()

        self.root.title(
            f"{self.app_name} Audio Output"
        )

        self.root.geometry("380x125")
        self.root.resizable(False, False)

        title_label = tk.Label(
            self.root,
            text=self.app_name,
            font=(
                "TkDefaultFont",
                13,
                "bold",
            ),
        )

        title_label.pack(
            pady=(12, 2)
        )

        self.status_label = tk.Label(
            self.root,
            text="待機中",
        )

        self.status_label.pack(
            pady=(0, 8)
        )

        self.meter = tk.Canvas(
            self.root,
            width=340,
            height=34,
            highlightthickness=0,
        )

        self.meter.pack()

        bar_width = 14
        gap = 4
        start_x = 4

        for index in range(
            METER_BARS
        ):
            x1 = (
                start_x
                + index
                * (bar_width + gap)
            )

            bar = self.meter.create_rectangle(
                x1,
                26,
                x1 + bar_width,
                30,
                fill="#b0b0b0",
                outline="",
            )

            self.bars.append(bar)

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.root.iconify,
        )

    def _start_audio_stream(self):
        """
        常駐音声ストリームを開始する。
        """
        self.stream = sd.OutputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            blocksize=BLOCK_SIZE,
            callback=self._audio_callback,
        )

        self.stream.start()

    def _poll_commands(self):
        """
        親プロセスからの指示を確認する。
        """
        if not self.running:
            return

        while True:
            try:
                command = (
                    self.command_queue.get_nowait()
                )
            except queue.Empty:
                break

            command_type = command.get(
                "type"
            )

            if command_type == "play":
                self._handle_play_command(
                    command
                )

            elif command_type == "stop":
                self.running = False
                self.root.quit()
                return

        self._send_completed_events()

        self.root.after(
            20,
            self._poll_commands,
        )

    def _handle_play_command(
        self,
        command: dict,
    ):
        """
        WAV再生指示をキューへ追加する。
        """
        item_id = command["id"]
        wav_data = command["wav"]

        try:
            samples = self._decode_wav(
                wav_data
            )

        except Exception as exc:
            self.event_queue.put({
                "type": "playback_error",
                "id": item_id,
                "message": str(exc),
            })
            return

        self.playback_queue.put({
            "id": item_id,
            "samples": samples,
        })

    def _send_completed_events(self):
        """
        再生完了イベントを親プロセスへ返す。
        """
        while True:
            try:
                item_id = (
                    self.completed_queue.get_nowait()
                )
            except queue.Empty:
                break

            self.event_queue.put({
                "type": "completed",
                "id": item_id,
            })

    def _audio_callback(
        self,
        outdata,
        frames,
        time_info,
        status,
    ):
        """
        PortAudioから呼び出される音声出力処理。
        """
        outdata.fill(0)

        written = 0

        while written < frames:
            if self.current_item is None:
                try:
                    self.current_item = (
                        self.playback_queue.get_nowait()
                    )
                    self.current_position = 0

                except queue.Empty:
                    break

            samples = self.current_item[
                "samples"
            ]

            remaining = (
                len(samples)
                - self.current_position
            )

            if remaining <= 0:
                self._complete_current_item()
                continue

            count = min(
                frames - written,
                remaining,
            )

            start = self.current_position
            end = start + count

            outdata[
                written:written + count
            ] = samples[start:end]

            written += count
            self.current_position = end

            if self.current_position >= len(
                samples
            ):
                self._complete_current_item()

        level = float(
            np.sqrt(
                np.mean(
                    np.square(outdata)
                )
            )
        )

        self.level = min(
            level * 5.0,
            1.0,
        )

    def _complete_current_item(self):
        """
        現在の再生項目を完了状態にする。
        """
        if self.current_item is None:
            return

        self.completed_queue.put(
            self.current_item["id"]
        )

        self.current_item = None
        self.current_position = 0

    def _update_meter(self):
        """
        レベルメーターと状態表示を更新する。
        """
        if not self.running:
            return

        active_bars = round(
            self.level * METER_BARS
        )

        playing = (
            self.current_item is not None
            or not self.playback_queue.empty()
        )

        self.status_label.config(
            text=(
                "再生中"
                if playing
                else "待機中"
            )
        )

        for index, bar in enumerate(
            self.bars
        ):
            active = (
                index < active_bars
            )

            height = (
                26
                if active
                else 4
            )

            x1, _, x2, _ = (
                self.meter.coords(bar)
            )

            self.meter.coords(
                bar,
                x1,
                30 - height,
                x2,
                30,
            )

            self.meter.itemconfig(
                bar,
                fill=(
                    "#202020"
                    if active
                    else "#b0b0b0"
                ),
            )

        self.root.after(
            50,
            self._update_meter,
        )

    def _decode_wav(
        self,
        wav_data: bytes,
    ) -> np.ndarray:
        """
        WAVデータを48kHz・ステレオ・float32へ変換する。
        """
        with wave.open(
            io.BytesIO(wav_data),
            "rb",
        ) as wav_file:
            channels = wav_file.getnchannels()
            sample_width = (
                wav_file.getsampwidth()
            )
            sample_rate = (
                wav_file.getframerate()
            )
            frame_count = (
                wav_file.getnframes()
            )

            raw = wav_file.readframes(
                frame_count
            )

        if sample_width != 2:
            raise RuntimeError(
                "現在対応しているWAV形式は"
                "16bit PCMのみです。"
            )

        samples = np.frombuffer(
            raw,
            dtype="<i2",
        ).astype(np.float32)

        samples /= 32768.0

        if channels > 1:
            samples = samples.reshape(
                -1,
                channels,
            )
        else:
            samples = samples.reshape(
                -1,
                1,
            )

        samples = self._convert_channels(
            samples
        )

        if sample_rate != SAMPLE_RATE:
            samples = self._resample(
                samples,
                sample_rate,
                SAMPLE_RATE,
            )

        return np.ascontiguousarray(
            samples,
            dtype=np.float32,
        )

    def _convert_channels(
        self,
        samples: np.ndarray,
    ) -> np.ndarray:
        """
        音声をステレオへ変換する。
        """
        channels = samples.shape[1]

        if channels == CHANNELS:
            return samples

        if channels == 1:
            return np.repeat(
                samples,
                CHANNELS,
                axis=1,
            )

        mono = np.mean(
            samples,
            axis=1,
            keepdims=True,
        )

        return np.repeat(
            mono,
            CHANNELS,
            axis=1,
        )

    def _resample(
        self,
        samples: np.ndarray,
        source_rate: int,
        target_rate: int,
    ) -> np.ndarray:
        """
        線形補間でサンプリングレートを変換する。
        """
        source_length = len(samples)

        if source_length == 0:
            return samples

        target_length = round(
            source_length
            * target_rate
            / source_rate
        )

        source_positions = np.linspace(
            0.0,
            1.0,
            source_length,
            endpoint=False,
        )

        target_positions = np.linspace(
            0.0,
            1.0,
            target_length,
            endpoint=False,
        )

        result = np.empty(
            (
                target_length,
                CHANNELS,
            ),
            dtype=np.float32,
        )

        for channel in range(
            CHANNELS
        ):
            result[:, channel] = np.interp(
                target_positions,
                source_positions,
                samples[:, channel],
            )

        return result

    def _shutdown(self):
        """
        音声ストリームとウィンドウを終了する。
        """
        self.running = False

        if self.stream is not None:
            try:
                self.stream.stop()
            finally:
                self.stream.close()

            self.stream = None

        if self.root is not None:
            try:
                self.root.destroy()
            except tk.TclError:
                pass

            self.root = None
