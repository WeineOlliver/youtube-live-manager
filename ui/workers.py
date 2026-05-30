"""QThread workers for background YouTube API operations."""
from PyQt6.QtCore import QThread, pyqtSignal

from core import youtube_api as yt


class CreateLivesWorker(QThread):
    log_line = pyqtSignal(str)
    done = pyqtSignal(dict)
    failed = pyqtSignal()
    aborted = pyqtSignal()

    def __init__(self, config: dict):
        super().__init__()
        self._cfg = config
        self._stop_requested = False
        self._created: dict = {}

    def request_stop(self):
        self._stop_requested = True

    def _run_cleanup(self, youtube):
        """Delete all resources created so far. Does not emit any signal."""
        if not self._created:
            return
        self.log_line.emit("🗑️ Revertendo recursos criados...")
        errors = yt.cleanup_resources(youtube, self._created)
        for err in errors:
            self.log_line.emit(f"⚠️ Erro ao deletar: {err}")
        if not errors:
            self.log_line.emit("✅ Recursos removidos com sucesso")

    def run(self):
        cfg = self._cfg
        test = cfg["test_mode"]
        resolution = "1080p" if test else "1440p"
        privacy = "private" if test else "public"
        latency = "ultraLow" if test else "low"
        self._created = {}

        youtube = None
        try:
            youtube = yt.get_youtube_client()

            # Selective creation for Full HD
            if cfg.get("enable_fhd", True):
                self.log_line.emit("⏳ Criando stream Full HD...")
                stream_fhd = yt.create_live_stream(youtube, yt.RTMP_STREAM_FULLHD, resolution)
                self._created["stream_fhd_id"] = stream_fhd["id"]
                self.log_line.emit(f"✅ Stream Full HD criado — ID: {stream_fhd['id']}")
                if self._stop_requested:
                    self._run_cleanup(youtube)
                    self.aborted.emit()
                    return

                title = cfg["title"]
                desc = cfg["description"]

                self.log_line.emit("⏳ Criando broadcast Full HD...")
                bc_fhd = yt.create_broadcast(youtube, title, desc, privacy, latency)
                yt.bind_broadcast(youtube, bc_fhd["id"], stream_fhd["id"])
                self._created["bc_fhd_id"] = bc_fhd["id"]
                self.log_line.emit(f"✅ Broadcast Full HD criado — ID: {bc_fhd['id']}")
                if self._stop_requested:
                    self._run_cleanup(youtube)
                    self.aborted.emit()
                    return

                self.log_line.emit("⏳ Enviando thumbnail Full HD...")
                yt.upload_thumbnail(youtube, bc_fhd["id"], cfg["thumbnail_normal"])
                self.log_line.emit("✅ Thumbnail Full HD enviada")

                self.log_line.emit("⏳ Atualizando tags Full HD...")
                yt.update_tags(youtube, bc_fhd["id"], cfg["tags"])
                self.log_line.emit("✅ Tags Full HD atualizadas")
                if self._stop_requested:
                    self._run_cleanup(youtube)
                    self.aborted.emit()
                    return

            # Selective creation for Shorts
            if cfg.get("enable_shorts", True):
                self.log_line.emit("⏳ Criando stream Shorts...")
                stream_shorts = yt.create_live_stream(youtube, yt.RTMP_STREAM_SHORTS, resolution)
                self._created["stream_shorts_id"] = stream_shorts["id"]
                self.log_line.emit(f"✅ Stream Shorts criado — ID: {stream_shorts['id']}")
                if self._stop_requested:
                    self._run_cleanup(youtube)
                    self.aborted.emit()
                    return

                title = cfg["title"]
                desc = cfg["description"]
                title_shorts = f"{title} | SHORTS"
                
                self.log_line.emit("⏳ Criando broadcast Shorts...")
                bc_shorts = yt.create_broadcast(youtube, title_shorts, desc, privacy, latency)
                yt.bind_broadcast(youtube, bc_shorts["id"], stream_shorts["id"])
                self._created["bc_shorts_id"] = bc_shorts["id"]
                self.log_line.emit(f"✅ Broadcast Shorts criado — ID: {bc_shorts['id']}")
                if self._stop_requested:
                    self._run_cleanup(youtube)
                    self.aborted.emit()
                    return

                self.log_line.emit("⏳ Enviando thumbnail Shorts...")
                yt.upload_thumbnail(youtube, bc_shorts["id"], cfg["thumbnail_shorts"])
                self.log_line.emit("✅ Thumbnail Shorts enviada")

                self.log_line.emit("⏳ Atualizando tags Shorts...")
                yt.update_tags(youtube, bc_shorts["id"], cfg["tags"])
                self.log_line.emit("✅ Tags Shorts atualizadas")

        except Exception as e:
            self.log_line.emit(f"❌ Erro: {e}")
            if youtube is not None:
                self._run_cleanup(youtube)
            self.failed.emit()
            return

        self.done.emit(self._created)


class DeleteResourcesWorker(QThread):
    log_line = pyqtSignal(str)
    done = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, ids: dict):
        super().__init__()
        self._ids = ids

    def run(self):
        try:
            youtube = yt.get_youtube_client()
            self.log_line.emit("🗑️ Deletando streams de teste...")
            errors = yt.cleanup_resources(youtube, self._ids)
            for err in errors:
                self.log_line.emit(f"⚠️ {err}")
            if errors:
                self.failed.emit(f"{len(errors)} recurso(s) não puderam ser deletados")
            else:
                self.log_line.emit("✅ Streams de teste deletados com sucesso")
                self.done.emit()
        except Exception as e:
            self.failed.emit(f"❌ Erro ao deletar: {e}")
