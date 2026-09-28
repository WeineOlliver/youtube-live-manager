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

    def _abort_if_requested(self, youtube) -> bool:
        if not self._stop_requested:
            return False
        self._run_cleanup(youtube)
        self.aborted.emit()
        return True

    def run(self):
        cfg = self._cfg
        test = cfg["test_mode"]
        privacy = "private" if test else "public"
        latency = "ultraLow" if test else "low"
        self._created = {}

        stream_key = cfg.get("stream_key", "").strip()
        if not stream_key:
            self.log_line.emit("⚠️ Informe a chave RTMP antes de criar a live")
            self.failed.emit()
            return

        youtube = None
        try:
            youtube = yt.get_youtube_client()

            self.log_line.emit("⏳ Localizando chave RTMP na conta...")
            stream_id = yt.find_stream_id_by_key(youtube, stream_key)
            self.log_line.emit(f"✅ Chave RTMP encontrada — ID: {stream_id}")
            if self._abort_if_requested(youtube):
                return

            self.log_line.emit("⏳ Criando broadcast...")
            bc = yt.create_broadcast(youtube, cfg["title"], cfg["description"], privacy, latency)
            # Register before binding so a failed bind still gets rolled back.
            self._created["bc_id"] = bc["id"]
            yt.bind_broadcast(youtube, bc["id"], stream_id)
            self.log_line.emit(f"✅ Broadcast criado e vinculado — ID: {bc['id']}")
            if self._abort_if_requested(youtube):
                return

            self.log_line.emit("⏳ Enviando thumbnail...")
            yt.upload_thumbnail(youtube, bc["id"], cfg["thumbnail_normal"])
            self.log_line.emit("✅ Thumbnail enviada")
            if self._abort_if_requested(youtube):
                return

            self.log_line.emit("⏳ Atualizando tags...")
            yt.update_tags(youtube, bc["id"], cfg["tags"])
            self.log_line.emit("✅ Tags atualizadas")

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
            self.log_line.emit("🗑️ Deletando live de teste...")
            errors = yt.cleanup_resources(youtube, self._ids)
            for err in errors:
                self.log_line.emit(f"⚠️ {err}")
            if errors:
                self.failed.emit(f"{len(errors)} recurso(s) não puderam ser deletados")
            else:
                self.log_line.emit("✅ Live de teste deletada com sucesso")
                self.done.emit()
        except Exception as e:
            self.failed.emit(f"❌ Erro ao deletar: {e}")
