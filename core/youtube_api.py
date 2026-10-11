# scripts/youtube-live-manager/core/youtube_api.py
import glob
import os
import pickle
from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
_secrets = glob.glob(os.path.join(BASE_DIR, "client-secret", "client_secret_*.json"))
CLIENT_SECRETS_FILE = _secrets[0] if _secrets else None
TOKEN_PATH = os.path.join(BASE_DIR, "client-secret", "token_youtube.pickle")
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

def get_token_status() -> tuple[bool, str]:
    """Returns (is_valid, display_label) for the top bar."""
    if not os.path.exists(TOKEN_PATH):
        return False, "Token não encontrado"
    with open(TOKEN_PATH, "rb") as f:
        creds = pickle.load(f)
    if creds.valid:
        if creds.expiry:
            # google-auth stores expiry as naive UTC; compare with utcnow()
            now = datetime.utcnow()
            mins = int((creds.expiry - now).total_seconds() / 60)
            return True, f"Token válido — expira em {mins} min"
        return True, "Token válido"
    return False, "Token expirado"


def refresh_token() -> tuple[bool, str]:
    """Refresh or re-authenticate. Returns (success, message)."""
    if CLIENT_SECRETS_FILE is None:
        return False, "Arquivo client_secret_*.json não encontrado em client-secret/"
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
        creds = flow.run_local_server(port=53999)

    with open(TOKEN_PATH, "wb") as f:
        pickle.dump(creds, f)
    return True, "Token renovado com sucesso"


def get_youtube_client():
    """Return an authenticated YouTube API v3 client."""
    if not os.path.exists(TOKEN_PATH):
        raise FileNotFoundError("Token não encontrado. Use 'Renovar' para autenticar.")
    with open(TOKEN_PATH, "rb") as f:
        creds = pickle.load(f)
    if not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)
    return build("youtube", "v3", credentials=creds)


def find_stream_id_by_key(youtube, stream_key: str) -> str:
    """Return the ID of the account's live stream whose RTMP key matches stream_key."""
    stream_key = stream_key.strip()
    page_token = None
    while True:
        response = youtube.liveStreams().list(
            part="id,cdn",
            mine=True,
            maxResults=50,
            pageToken=page_token,
        ).execute()
        for item in response.get("items", []):
            if item["cdn"]["ingestionInfo"]["streamName"] == stream_key:
                return item["id"]
        page_token = response.get("nextPageToken")
        if not page_token:
            raise ValueError("Chave RTMP não encontrada na conta")


def create_broadcast(
    youtube,
    title: str,
    description: str,
    privacy: str = "public",
    latency: str = "low",
) -> dict:
    """Create a live broadcast scheduled 2 minutes from now and return the broadcast dict."""
    start_time = (
        datetime.now(timezone.utc) + timedelta(minutes=2)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    return youtube.liveBroadcasts().insert(
        part="snippet,status,contentDetails",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "scheduledStartTime": start_time,
            },
            "status": {"privacyStatus": privacy},
            "contentDetails": {
                "latencyPreference": latency,
                "monitorStream": {"enableMonitorStream": True},
            },
        },
    ).execute()


def bind_broadcast(youtube, broadcast_id: str, stream_id: str) -> None:
    """Bind a broadcast to a stream so they are associated."""
    youtube.liveBroadcasts().bind(
        part="id,contentDetails",
        id=broadcast_id,
        streamId=stream_id,
    ).execute()


def upload_thumbnail(youtube, video_id: str, thumb_path: str) -> None:
    """Upload a thumbnail image file to the given video ID."""
    youtube.thumbnails().set(
        videoId=video_id,
        media_body=MediaFileUpload(thumb_path),
    ).execute()


def update_tags(youtube, video_id: str, tags: list[str]) -> None:
    """Fetch the current snippet, replace tags, and update the video."""
    response = youtube.videos().list(part="snippet", id=video_id).execute()
    if not response.get("items"):
        raise ValueError(f"Video {video_id} not found")
    snippet = response["items"][0]["snippet"]
    snippet["tags"] = tags
    youtube.videos().update(
        part="snippet",
        body={"id": video_id, "snippet": snippet},
    ).execute()


def get_stream_status(youtube, stream_id: str) -> str:
    """Returns streamStatus: 'active', 'inactive', 'testing', or 'ready'."""
    response = youtube.liveStreams().list(part="status", id=stream_id).execute()
    if not response.get("items"):
        return "inactive"
    return response["items"][0]["status"]["streamStatus"]


def transition_broadcast(youtube, broadcast_id: str, status: str = "live") -> None:
    youtube.liveBroadcasts().transition(
        broadcastStatus=status,
        id=broadcast_id,
        part="id,status",
    ).execute()


def delete_broadcast(youtube, broadcast_id: str) -> None:
    youtube.liveBroadcasts().delete(id=broadcast_id).execute()


def cleanup_resources(youtube, ids: dict) -> list[str]:
    """
    Deletes the broadcasts in ids["bc_fhd_id"] / ids["bc_shorts_id"], if present.
    The fixed RTMP streams are never deleted. Returns a list of error strings.
    """
    errors = []
    for key in ("bc_fhd_id", "bc_shorts_id"):
        broadcast_id = ids.get(key)
        if broadcast_id:
            try:
                delete_broadcast(youtube, broadcast_id)
            except Exception as e:
                errors.append(f"{key}: {e}")
    return errors
