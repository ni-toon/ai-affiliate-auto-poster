"""
スケジューラースクリプト
1日5記事の自動投稿を継続的に実行する
"""

import asyncio
import sys
import os
import signal
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main_controller import MainController

class AutoPosterScheduler:
    def __init__(self):
        self.controller = MainController()
        self.running = True
    
    def signal_handler(self, signum, frame):
        """シグナルハンドラー（Ctrl+Cで停止）"""
        print("\n停止シグナルを受信しました。プログラムを終了します...")
        self.running = False
    
    async def run_continuous(self):
        """継続的な実行"""
        print("AI自動投稿システム開始")
        print("停止するにはCtrl+Cを押してください")
        
        # シグナルハンドラーを設定
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            while self.running:
                current_time = datetime.now()
                print(f"\n[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] システム稼働中...")
                
                # 1日のスケジュールを実行
                await self.controller.run_daily_schedule()
                
                # 次の日まで待機（24時間）
                if self.running:
                    print("次の実行まで24時間待機します...")
                    await asyncio.sleep(24 * 60 * 60)  # 24時間
        
        except KeyboardInterrupt:
            print("\nキーボード割り込みを受信しました")
        except Exception as e:
            print(f"予期しないエラー: {e}")
        finally:
            print("システムを終了します")
    
    def run(self):
        """スケジューラーを開始"""
        try:
            asyncio.run(self.run_continuous())
        except KeyboardInterrupt:
            print("\nプログラムが中断されました")
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

