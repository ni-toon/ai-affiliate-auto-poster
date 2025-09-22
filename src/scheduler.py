"""
スケジューラースクリプト
1日5記事の自動投稿を継続的に実行する
- Ctrl+C (SIGINT) で即座に安全終了できるように修正
- signal.signal による SIGINT 上書きを廃止（KeyboardInterrupt を素直に使う）
- 長時間待機は stop_event でもブレークできるように設計（将来の拡張用）
"""

import asyncio
import sys
import os
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main_controller import MainController  # noqa: E402


class AutoPosterScheduler:
    def __init__(self):
        self.controller = MainController()
        # いまは Ctrl+C で KeyboardInterrupt を使うが、
        # 将来的に外部シグナルやUIからの停止要求を扱う場合に備えた stop_event
        self.stop_event = asyncio.Event()

    async def _sleep_until_next(self, seconds: int) -> None:
        """
        長時間スリープ。stop_event が立ったら早期解除。
        Ctrl+C では KeyboardInterrupt がルートで発生し、asyncio.run がキャンセルをかける。
        """
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
        """継続的な実行（Ctrl+Cで即終了できる）"""
        print("AI自動投稿システム開始")
        print("停止するには Ctrl+C を押してください")

        try:
            while not self.stop_event.is_set():
                current_time = datetime.now()
                print(f"\n[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] システム稼働中...")

                # 1日のスケジュールを実行
                # ※ run_daily_schedule 内部でawaitが多いなら、Ctrl+CでKeyboardInterruptが飛んで即座に抜ける
                await self.controller.run_daily_schedule()

                # 次の実行まで待機（12時間）
                if not self.stop_event.is_set():
                    print("次の実行まで12時間待機します...")
                    try:
                        await asyncio.sleep(12 * 60 * 60)
                    except asyncio.CancelledError:
                        # asyncio.run によるキャンセル等でここに来ることもある
                        break

        finally:
            print("システムを終了します")

    def run(self):
        """スケジューラーを開始"""
        try:
            asyncio.run(self.run_continuous())
        except KeyboardInterrupt:
            # Ctrl+C でここに来る。即座にプロセスを抜ける。
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
    import contextlib  # run_continuous 内の suppress 用
    main()
