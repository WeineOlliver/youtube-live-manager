"""QThread workers for background YouTube API operations."""
import time
from PyQt6.QtCore import QThread, pyqtSignal

from core import youtube_api as yt
from core.poll_automation import create_poll


class CreateLivesWorker(QThread):
    log_line = pyqtSignal(str)
    done = pyqtSignal(dict)
    failed = pyqtSignal()

    def __init__(self, config: dict):
        super().__init__()
        self._cfg = config

    def run(self):
        cfg = self._cfg
        test = cfg["test_mode"]
        resolution = "1080p" if test else "1440p"
        privacy = "private" if test else "public"
        latency = "ultraLow" if test else "low"

        try:
            youtube = yt.get_youtube_client()

            self.log_line.emit("⏳ Criando stream Full HD...")
            stream_fhd = yt.create_live_stream(youtube, yt.RTMP_STREAM_FULLHD, resolution)
            self.log_line.emit(f"✅ Stream Full HD criado — ID: {stream_fhd['id']}")

            self.log_line.emit("⏳ Criando stream Shorts...")
            stream_shorts = yt.create_live_stream(youtube, yt.RTMP_STREAM_SHORTS, resolution)
            self.log_line.emit(f"✅ Stream Shorts criado — ID: {stream_shorts['id']}")

            title = cfg["title"]
            desc = cfg["description"]

            self.log_line.emit("⏳ Criando broadcast Full HD...")
            bc_fhd = yt.create_broadcast(youtube, title, desc, privacy, latency)
            yt.bind_broadcast(youtube, bc_fhd["id"], stream_fhd["id"])
            self.log_line.emit(f"✅ Broadcast Full HD criado — ID: {bc_fhd['id']}")

            self.log_line.emit("⏳ Enviando thumbnail Full HD...")
            yt.upload_thumbnail(youtube, bc_fhd["id"], cfg["thumbnail_normal"])
            self.log_line.emit("✅ Thumbnail Full HD enviada")

            self.log_line.emit("⏳ Atualizando tags Full HD...")
            yt.update_tags(youtube, bc_fhd["id"], cfg["tags"])
            self.log_line.emit("✅ Tags Full HD atualizadas")

            title_shorts = f"{title} | SHORTS"
            self.log_line.emit("⏳ Criando broadcast Shorts...")
            bc_shorts = yt.create_broadcast(youtube, title_shorts, desc, privacy, latency)
            yt.bind_broadcast(youtube, bc_shorts["id"], stream_shorts["id"])
            self.log_line.emit(f"✅ Broadcast Shorts criado — ID: {bc_shorts['id']}")

            self.log_line.emit("⏳ Enviando thumbnail Shorts...")
            yt.upload_thumbnail(youtube, bc_shorts["id"], cfg["thumbnail_shorts"])
            self.log_line.emit("✅ Thumbnail Shorts enviada")

            self.log_line.emit("⏳ Atualizando tags Shorts...")
            yt.update_tags(youtube, bc_shorts["id"], cfg["tags"])
            self.log_line.emit("✅ Tags Shorts atualizadas")

            # Poll automation — graceful failure
            self.log_line.emit("⏳ Configurando enquete Full HD...")
            err = create_poll(
                bc_fhd["id"],
                cfg["poll_fullhd_question"],
                cfg["poll_fullhd_options"],
            )
            if err:
                self.log_line.emit(f"⚠️ Enquete Full HD falhou — continuando normalmente\n   {err}")
            else:
                self.log_line.emit("✅ Enquete Full HD configurada")

            self.log_line.emit("⏳ Configurando enquete Shorts...")
            err = create_poll(
                bc_shorts["id"],
                cfg["poll_shorts_question"],
                cfg["poll_shorts_options"],
            )
            if err:
                self.log_line.emit(f"⚠️ Enquete Shorts falhou — continuando normalmente\n   {err}")
            else:
                self.log_line.emit("✅ Enquete Shorts configurada")

        except Exception as e:
            self.log_line.emit(f"❌ Erro: {e}")
            self.failed.emit()
            return

        self.done.emit({
            "stream_fhd_id": stream_fhd["id"],
            "stream_shorts_id": stream_shorts["id"],
            "bc_fhd_id": bc_fhd["id"],
            "bc_shorts_id": bc_shorts["id"],
        })


class ObsWatcherWorker(QThread):
    log_line = pyqtSignal(str)
    went_live = pyqtSignal()
    failed = pyqtSignal(str)

    POLL_INTERVAL_SECS = 5

    def __init__(self, stream_fhd_id: str, stream_shorts_id: str,
                 bc_fhd_id: str, bc_shorts_id: str):
        super().__init__()
        self._stream_fhd = stream_fhd_id
        self._stream_shorts = stream_shorts_id
        self._bc_fhd = bc_fhd_id
        self._bc_shorts = bc_shorts_id
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            youtube = yt.get_youtube_client()
        except Exception as e:
            self.failed.emit(f"❌ Falha ao autenticar para OBS watcher: {e}")
            return

        while not self._stop:
            try:
                status_fhd = yt.get_stream_status(youtube, self._stream_fhd)
                status_shorts = yt.get_stream_status(youtube, self._stream_shorts)
                self.log_line.emit(
                    f"⏳ Aguardando OBS... (Full HD: {status_fhd}, Shorts: {status_shorts})"
                )

                if status_fhd == "active" and status_shorts == "active":
                    self.log_line.emit("✅ OBS conectado! Iniciando lives ao vivo...")
                    yt.transition_broadcast(youtube, self._bc_fhd, "live")
                    yt.transition_broadcast(youtube, self._bc_shorts, "live")
                    self.log_line.emit("✅ Ambas as lives iniciadas ao vivo!")
                    self.went_live.emit()
                    return

            except Exception as e:
                self.failed.emit(f"❌ Erro no OBS watcher: {e}")
                return

            time.sleep(self.POLL_INTERVAL_SECS)
