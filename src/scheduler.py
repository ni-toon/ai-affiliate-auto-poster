"""
スケジューラースクリプト
1日5記事の自動投稿を継続的に実行する
- コアタイム内のみ実行（CORE_WINDOWS）
- Ctrl+C (SIGINT) で安全に終了
- signal.signal は使わず KeyboardInterrupt に任せる
- 長時間待機は stop_event でブレーク可能
"""

import asyncio
import sys
import os
import contextlib
from datetime import datetime, time, timedelta
from typing import List, Tuple

try:
    # Python 3.9+ 標準
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None  # Windows などで古い Python の場合は別途 tzlocal 等が必要

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main_controller import MainController  # noqa: E402


def _get_tz() -> object:
    tzname = os.getenv("TIMEZONE", "Asia/Tokyo")
    if ZoneInfo:
        return ZoneInfo(tzname)
    # もし ZoneInfo が無い古環境ならUTCで代替（実運用はZoneInfoを推奨）
    return None


def _parse_core_windows(spec: str) -> List[Tuple[time, time]]:
    """
    "HH:MM-HH:MM,HH:MM-HH:MM" を [(start, end), ...] にパース
    例: "09:00-12:00,14:00-18:00"
    """
    windows: List[Tuple[time, time]] = []
    if not spec:
        return windows
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            s, e = part.split("-")
            sh, sm = [int(x) for x in s.split(":")]
            eh, em = [int(x) for x in e.split(":")]
            windows.append((time(sh, sm), time(eh, em)))
        except Exception:
            raise ValueError(f"CORE_WINDOWS の書式が不正です: {part}")
    return windows


def _is_within_windows(now: datetime, windows: List[Tuple[time, time]]) -> bool:
    """now が任意の時間帯に入っているか"""
    t = now.timetz() if now.tzinfo else now.time()
    for start, end in windows:
        if start <= end:
            # 通常（同日内）
            if start <= t < end:
                return True
        else:
            # 跨日（例: 22:00-02:00）
            if t >= start or t < end:
                return True
    return False


def _next_window_start_on_or_after(ref_dt: datetime, windows: List[Tuple[time, time]]) -> datetime:
    """
    ref_dt 以降で最も早いコアタイム開始時刻を返す。
    コアタイムが存在しない日は翌日以降を検索（最大7日分）。
    """
    tz = ref_dt.tzinfo
    candidates: List[datetime] = []
    for d in range(0, 8):  # 最大1週間先まで検索
        day = (ref_dt + timedelta(days=d)).date()
        for start, end in windows:
            start_dt = datetime.combine(day, start, tz) if tz else datetime.combine(day, start)
            end_dt = datetime.combine(day, end, tz) if tz else datetime.combine(day, end)
            # 跨日窓の開始は day の start 時刻でOK（endは翌日）
            if start_dt >= ref_dt:
                candidates.append(start_dt)
        if candidates:
            return min(candidates)
    # 見つからない場合は 24時間後にフォールバック
    return ref_dt + timedelta(days=1)


def _seconds_until(dt: datetime, now: datetime) -> int:
    diff = (dt - now).total_seconds()
    return max(1, int(diff))


class AutoPosterScheduler:
    def __init__(self):
        self.controller = MainController()
        self.stop_event = asyncio.Event()

        # 設定
        self.tz = _get_tz()
        core_spec = os.getenv("CORE_WINDOWS", "09:00-21:00")
        self.core_windows = _parse_core_windows(core_spec)
        self.min_interval = timedelta(hours=float(os.getenv("MIN_INTERVAL_HOURS", "12")))

        if not self.core_windows:
            raise ValueError("CORE_WINDOWS が未設定か不正です。例: 09:00-12:00,14:00-18:00")

    async def _sleep_until_next(self, seconds: int) -> None:
        sleep_task = asyncio.create_task(asyncio.sleep(seconds))
        stop_task = asyncio.create_task(self.stop_event.wait())
        done, pending = await asyncio.wait(
            {sleep_task, stop_task}, return_when=asyncio.FIRST_COMPLETED
        )
        for t in pending:
            t.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await t

    async def run_continuous(self):
        """継続実行（コアタイム内のみ投稿）"""
        tzname = self.tz.key if getattr(self.tz, "key", None) else str(self.tz or "localtime")
        print("AI自動投稿システム開始")
        print(f"タイムゾーン: {tzname}")
        print(f"コアタイム: {', '.join([f'{s.strftime('%H:%M')}-{e.strftime('%H:%M')}' for s, e in self.core_windows])}")
        print("停止するには Ctrl+C を押してください")

        try:
            next_earliest = None  # 直近の「最短間隔を満たす時刻」

            while not self.stop_event.is_set():
                now = datetime.now(self.tz)
                print(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] 稼働チェック")

                # まだ最短間隔を満たしていなければ、そこまで待機
                if next_earliest and now < next_earliest:
                    if _is_within_windows(now, self.core_windows):
                        # コアタイム内だがインターバル未達 → 残り時間だけ待機
                        wait_sec = _seconds_until(next_earliest, now)
                        print(f"最短間隔待ち: {wait_sec//60}分 待機します（{next_earliest.strftime('%H:%M:%S')} まで）")
                        await self._sleep_until_next(wait_sec)
                        continue
                    else:
                        # コアタイム外 → 次の窓開始まで待機
                        start = _next_window_start_on_or_after(now, self.core_windows)
                        wait_sec = _seconds_until(start, now)
                        print(f"コアタイム外。次の開始まで待機: {wait_sec//60}分（{start.strftime('%Y-%m-%d %H:%M:%S')}）")
                        await self._sleep_until_next(wait_sec)
                        continue

                # ここに来たら、インターバル条件は満たした
                if not _is_within_windows(now, self.core_windows):
                    # コアタイム外なら、次の開始まで待機
                    start = _next_window_start_on_or_after(now, self.core_windows)
                    wait_sec = _seconds_until(start, now)
                    print(f"コアタイム外。次の開始まで待機: {wait_sec//60}分（{start.strftime('%Y-%m-%d %H:%M:%S')}）")
                    await self._sleep_until_next(wait_sec)
                    continue

                # === ここで投稿実行 ===
                print("コアタイム内。1日のスケジュールを実行します...")
                await self.controller.run_daily_schedule()

                # 次回の earliest 実行可能時刻（最短間隔を確保）
                now = datetime.now(self.tz)
                next_earliest = now + self.min_interval

                # 次に実行するまでの待機：
                # 1) 単純に最短間隔を待つ
                # 2) ただし、その時刻がコアタイム外なら、次のコアタイム開始まで延ばす
                if _is_within_windows(next_earliest, self.core_windows):
                    wait_sec = _seconds_until(next_earliest, now)
                    print(f"次の実行まで最短間隔待機: {wait_sec//60}分（{next_earliest.strftime('%Y-%m-%d %H:%M:%S')}）")
                    await self._sleep_until_next(wait_sec)
                else:
                    start = _next_window_start_on_or_after(next_earliest, self.core_windows)
                    wait_sec = _seconds_until(start, now)
                    print(f"次の実行時刻がコアタイム外のため、次のコアタイム開始まで待機: {wait_sec//60}分（{start.strftime('%Y-%m-%d %H:%M:%S')}）")
                    await self._sleep_until_next(wait_sec)

        finally:
            print("システムを終了します")

    def run(self):
        """スケジューラーを開始"""
        try:
            asyncio.run(self.run_continuous())
        except KeyboardInterrupt:
            print("\n停止シグナルを受信しました。プログラムを終了します...")
        except Exception as e:
            print(f"実行エラー: {e}")


def main():
    """メイン関数"""
    print("=" * 50)
    print("AI自動投稿システム スケジューラー")
    print("=" * 50)

    scheduler = AutoPosterScheduler()
    scheduler.run()


if __name__ == "__main__":
    main()
