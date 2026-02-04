"""Schedule tracker for YouTube video uploads.

Tracks the next available publish date for automatic scheduling.
Uses file-based tracking with YouTube API fallback.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

try:
    from rich.console import Console
    console = Console()
except ImportError:
    class _Console:
        def print(self, msg): print(msg)
    console = _Console()


class ScheduleTracker:
    """Track and manage YouTube video publish schedule."""

    def __init__(self, tracker_path: Optional[str] = None):
        """Initialize the tracker.

        Args:
            tracker_path: Path to schedule_tracker.json. Defaults to data/schedule_tracker.json.
        """
        root = Path(__file__).parent.parent
        self.tracker_path = Path(tracker_path or root / "data" / "schedule_tracker.json")
        self.publish_hour_utc = 23  # 6 PM EST = 23:00 UTC
        self.publish_minute = 0

    def _load(self) -> dict:
        """Load tracker data from file."""
        if self.tracker_path.exists():
            try:
                return json.loads(self.tracker_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save(self, data: dict):
        """Save tracker data to file."""
        self.tracker_path.parent.mkdir(parents=True, exist_ok=True)
        self.tracker_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get_next_publish_date(self, youtube_service=None) -> datetime:
        """Get the next available publish date.

        Primary: Read from tracker file.
        Fallback: Query YouTube API for last scheduled video.

        Args:
            youtube_service: Optional YouTube API service for fallback query.

        Returns:
            Next publish datetime in UTC.
        """
        data = self._load()

        # Primary: Use tracked date if available
        if "next_publish" in data:
            try:
                next_date = datetime.fromisoformat(data["next_publish"].replace("Z", "+00:00"))
                # Ensure it's in the future
                now = datetime.now(timezone.utc)
                if next_date > now:
                    console.print(f"[cyan]Schedule tracker: next publish {next_date.strftime('%b %d, %Y %H:%M UTC')}[/cyan]")
                    return next_date
                else:
                    console.print("[yellow]Tracked date is in the past, querying YouTube...[/yellow]")
            except (ValueError, TypeError):
                console.print("[yellow]Invalid tracker date, querying YouTube...[/yellow]")

        # Fallback: Query YouTube API
        if youtube_service:
            last_scheduled = self._find_last_scheduled_video(youtube_service)
            if last_scheduled:
                next_date = last_scheduled + timedelta(days=1)
                console.print(f"[cyan]From YouTube API: next publish {next_date.strftime('%b %d, %Y %H:%M UTC')}[/cyan]")
                return next_date

        # Ultimate fallback: Tomorrow at publish time
        now = datetime.now(timezone.utc)
        tomorrow = now.replace(
            hour=self.publish_hour_utc,
            minute=self.publish_minute,
            second=0,
            microsecond=0
        ) + timedelta(days=1)
        console.print(f"[yellow]No schedule data found, defaulting to {tomorrow.strftime('%b %d, %Y %H:%M UTC')}[/yellow]")
        return tomorrow

    def _find_last_scheduled_video(self, youtube_service) -> Optional[datetime]:
        """Query YouTube API to find the last scheduled video's publish date.

        Args:
            youtube_service: Authenticated YouTube API service.

        Returns:
            Datetime of the last scheduled video, or None if not found.
        """
        try:
            # Get channel's uploads playlist
            channels_response = youtube_service.channels().list(
                part="contentDetails",
                mine=True
            ).execute()

            if not channels_response.get("items"):
                return None

            uploads_playlist_id = channels_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

            # Get recent videos with their status
            videos_response = youtube_service.playlistItems().list(
                part="snippet,status",
                playlistId=uploads_playlist_id,
                maxResults=50
            ).execute()

            # Find videos with scheduled publish dates
            scheduled_dates = []
            video_ids = [item["snippet"]["resourceId"]["videoId"] for item in videos_response.get("items", [])]

            if video_ids:
                # Get detailed status for these videos
                videos_detail = youtube_service.videos().list(
                    part="status",
                    id=",".join(video_ids[:50])
                ).execute()

                for video in videos_detail.get("items", []):
                    status = video.get("status", {})
                    publish_at = status.get("publishAt")
                    if publish_at:
                        try:
                            dt = datetime.fromisoformat(publish_at.replace("Z", "+00:00"))
                            scheduled_dates.append(dt)
                        except ValueError:
                            pass

            if scheduled_dates:
                last_scheduled = max(scheduled_dates)
                console.print(f"[dim]Found {len(scheduled_dates)} scheduled videos, latest: {last_scheduled.strftime('%b %d')}[/dim]")
                return last_scheduled

            return None

        except Exception as e:
            console.print(f"[yellow]YouTube API query failed: {e}[/yellow]")
            return None

    def advance_schedule(self, scheduled_date: datetime, video_id: str = None, title: str = None):
        """Advance the schedule to the next day after a successful upload.

        Args:
            scheduled_date: The date that was just used for scheduling.
            video_id: Optional video ID that was scheduled.
            title: Optional video title.
        """
        next_date = scheduled_date + timedelta(days=1)

        data = {
            "next_publish": next_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "publish_time_utc": f"{self.publish_hour_utc:02d}:{self.publish_minute:02d}",
            "last_scheduled_date": scheduled_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        if video_id:
            data["last_scheduled_video"] = video_id
        if title:
            data["last_scheduled_title"] = title

        self._save(data)
        console.print(f"[green]Schedule advanced to {next_date.strftime('%b %d, %Y')}[/green]")

    def set_next_date(self, date_str: str) -> bool:
        """Manually set the next publish date.

        Args:
            date_str: Date string in YYYY-MM-DD format.

        Returns:
            True if successful.
        """
        try:
            # Parse the date and set to publish time
            date = datetime.strptime(date_str, "%Y-%m-%d")
            next_date = date.replace(
                hour=self.publish_hour_utc,
                minute=self.publish_minute,
                second=0,
                tzinfo=timezone.utc
            )

            data = self._load()
            data["next_publish"] = next_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            data["publish_time_utc"] = f"{self.publish_hour_utc:02d}:{self.publish_minute:02d}"
            self._save(data)

            console.print(f"[green]Next publish date set to {next_date.strftime('%b %d, %Y %H:%M UTC')}[/green]")
            return True

        except ValueError as e:
            console.print(f"[red]Invalid date format. Use YYYY-MM-DD (e.g., 2026-02-21)[/red]")
            return False

    def get_status(self) -> Tuple[Optional[datetime], Optional[str], Optional[str]]:
        """Get current schedule status.

        Returns:
            Tuple of (next_publish_date, last_video_id, last_title)
        """
        data = self._load()

        next_date = None
        if "next_publish" in data:
            try:
                next_date = datetime.fromisoformat(data["next_publish"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        return (
            next_date,
            data.get("last_scheduled_video"),
            data.get("last_scheduled_title")
        )
