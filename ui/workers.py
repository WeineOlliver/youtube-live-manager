"""QThread workers for background YouTube API operations."""
import os

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

    def _create_live(self, youtube, kind: dict, privacy: str, latency: str) -> bool:
        """Create one broadcast bound to its fixed RTMP key. Returns False if aborted."""
        cfg = self._cfg
        label = kind["label"]

        self.log_line.emit(f"⏳ Localizando chave RTMP {label} na conta...")
        stream_id = yt.find_stream_id_by_key(youtube, kind["stream_key"])
        self.log_line.emit(f"✅ Chave RTMP {label} encontrada — ID: {stream_id}")
        if self._abort_if_requested(youtube):
            return False

        self.log_line.emit(f"⏳ Criando broadcast {label}...")
        bc = yt.create_broadcast(youtube, kind["title"], cfg["description"], privacy, latency)
        # Register before binding so a failed bind still gets rolled back.
        self._created[kind["id_key"]] = bc["id"]
        yt.bind_broadcast(youtube, bc["id"], stream_id)
        self.log_line.emit(f"✅ Broadcast {label} criado e vinculado — ID: {bc['id']}")
        self.log_line.emit(f"🔗 Studio {label}: {yt.studio_url(bc['id'])}")
        if self._abort_if_requested(youtube):
            return False

        self.log_line.emit(f"⏳ Enviando thumbnail {label}...")
        yt.upload_thumbnail(youtube, bc["id"], kind["thumbnail"])
        self.log_line.emit(f"✅ Thumbnail {label} enviada")
        if self._abort_if_requested(youtube):
            return False

        self.log_line.emit(f"⏳ Atualizando tags {label}...")
        yt.update_tags(youtube, bc["id"], cfg["tags"])
        self.log_line.emit(f"✅ Tags {label} atualizadas")
        return not self._abort_if_requested(youtube)

    def run(self):
        cfg = self._cfg
        test = cfg["test_mode"]
        privacy = "private" if test else "public"
        latency = "ultraLow" if test else "low"
        self._created = {}

        kinds = []
        if cfg.get("enable_fhd", True):
            kinds.append({
                "label": "Full HD",
                "id_key": "bc_fhd_id",
                "stream_key": cfg.get("stream_key", "").strip(),
                "title": cfg["title"],
                "thumbnail": cfg["thumbnail_normal"],
            })
        if cfg.get("enable_shorts", True):
            kinds.append({
                "label": "Shorts",
                "id_key": "bc_shorts_id",
                "stream_key": cfg.get("stream_key_shorts", "").strip(),
                "title": f"{cfg['title']} | SHORTS",
                "thumbnail": cfg["thumbnail_shorts"],
            })

        if not kinds:
            self.log_line.emit("⚠️ Selecione ao menos um tipo de live (FHD ou Shorts)")
            self.failed.emit()
            return
        missing = [k["label"] for k in kinds if not k["stream_key"]]
        if missing:
            self.log_line.emit(f"⚠️ Informe a chave RTMP {', '.join(missing)} antes de criar")
            self.failed.emit()
            return
        bad_thumbs = [k["label"] for k in kinds if not os.path.isfile(k["thumbnail"])]
        if bad_thumbs:
            self.log_line.emit(f"⚠️ Thumbnail {', '.join(bad_thumbs)} não encontrada — confira o caminho")
            self.failed.emit()
            return

        youtube = None
        try:
            youtube = yt.get_youtube_client()
            for kind in kinds:
                if not self._create_live(youtube, kind, privacy, latency):
                    return
        except Exception as e:
            self.log_line.emit(f"❌ Erro: {yt.describe_error(e)}")
            if youtube is not None:
                self._run_cleanup(youtube)
            self.failed.emit()
            return

        self.done.emit(self._created)


class DeleteResourcesWorker(QThread):
    log_line = pyqtSignal(str)
    done = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, id_batches: list[dict]):
        super().__init__()
        self._id_batches = id_batches

    def run(self):
        try:
            youtube = yt.get_youtube_client()
            self.log_line.emit("🗑️ Deletando lives de teste...")
            errors = []
            for ids in self._id_batches:
                errors += yt.cleanup_resources(youtube, ids)
            for err in errors:
                self.log_line.emit(f"⚠️ {err}")
            if errors:
                self.failed.emit(f"{len(errors)} recurso(s) não puderam ser deletados")
            else:
                self.log_line.emit("✅ Lives de teste deletadas com sucesso")
                self.done.emit()
        except Exception as e:
            self.failed.emit(f"❌ Erro ao deletar: {yt.describe_error(e)}")


class RenewTokenWorker(QThread):
    """Runs the OAuth refresh/login off the UI thread so the window never freezes."""
    done = pyqtSignal(bool, str)

    def run(self):
        try:
            ok, msg = yt.refresh_token()
        except Exception as e:
            ok, msg = False, f"Erro ao renovar: {yt.describe_error(e)}"
        self.done.emit(ok, msg)
