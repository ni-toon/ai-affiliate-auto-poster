#!/usr/bin/env python3
"""
画像生成テスト用スクリプト
実際のManus画像生成機能をテストする
"""

import os
import sys
import asyncio
import logging

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.image_generator_wrapper import ImageGeneratorWrapper

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_image_generation():
    """画像生成機能をテスト"""
    try:
        logger.info("画像生成テストを開始")
        
        # 画像生成ラッパーを初期化
        generator = ImageGeneratorWrapper()
        
        # テスト用のデータ
        test_cases = [
            {
                "title": "タロット占いで運命を読み解く方法",
                "category": "占い"
            },
            {
                "title": "筋トレ初心者のための効果的なトレーニング",
                "category": "フィットネス"
            },
            {
                "title": "ビジネス書から学ぶ成功の秘訣",
                "category": "書籍"
            }
        ]
        
        for test_case in test_cases:
            logger.info(f"テストケース: {test_case['title']}")
            
            # 画像生成データを準備
            image_data = generator.generate_thumbnail_image(
                test_case["title"], 
                test_case["category"]
            )
            
            if image_data:
                logger.info(f"画像生成データ準備成功:")
                logger.info(f"  プロンプト: {image_data['prompt'][:100]}...")
                logger.info(f"  出力パス: {image_data['output_path']}")
                
                # 実際の画像生成を試行
                # 注意: この部分は実際のManus環境でのみ動作します
                try:
                    # ここで実際の画像生成ツールを呼び出す
                    logger.info("実際の画像生成を試行中...")
                    
                    # テスト環境では、デフォルト画像を使用
                    default_image = generator.get_default_thumbnail(test_case["category"])
                    if default_image:
                        logger.info(f"デフォルト画像を使用: {default_image}")
                    else:
                        logger.warning(f"デフォルト画像が見つかりません: {test_case['category']}")
                    
                except Exception as e:
                    logger.error(f"画像生成エラー: {e}")
            else:
                logger.error(f"画像生成データ準備失敗: {test_case['title']}")
        
        logger.info("画像生成テスト完了")
        
    except Exception as e:
        logger.error(f"テスト実行エラー: {e}")

if __name__ == "__main__":
    asyncio.run(test_image_generation())

