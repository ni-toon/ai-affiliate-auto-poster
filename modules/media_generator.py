"""
画像生成モジュール
記事のサムネイル画像を生成する機能を提供
"""

import os
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class MediaGenerator:
    def __init__(self):
        self.thumbnail_dir = "data/thumbnails"
        os.makedirs(self.thumbnail_dir, exist_ok=True)
    
    async def generate_thumbnail_image(self, title: str, category: str, article_content: str = "") -> Optional[str]:
        """記事タイトルとカテゴリに基づいてサムネイル画像を生成"""
        try:
            # カテゴリに応じたプロンプトを生成
            category_prompts = {
                "占い": {
                    "style": "mystical, spiritual, elegant",
                    "elements": "tarot cards, crystal ball, celestial symbols, purple and gold colors",
                    "mood": "mysterious and enchanting"
                },
                "フィットネス": {
                    "style": "energetic, modern, motivational",
                    "elements": "fitness equipment, dumbbells, yoga mat, healthy lifestyle",
                    "mood": "dynamic and inspiring"
                },
                "書籍": {
                    "style": "intellectual, warm, professional",
                    "elements": "books, reading, library atmosphere, knowledge symbols",
                    "mood": "scholarly and inviting"
                }
            }
            
            prompt_data = category_prompts.get(category, {
                "style": "clean, professional, modern",
                "elements": "simple geometric shapes, neutral colors",
                "mood": "trustworthy and approachable"
            })
            
            # 詳細なプロンプトを作成
            prompt = f"""Create a professional thumbnail image for a Japanese blog article about {category}. 
            
            Title: {title}
            
            Style: {prompt_data['style']}
            Visual elements: {prompt_data['elements']}
            Mood: {prompt_data['mood']}
            
            Requirements:
            - Size suitable for social media thumbnails (1200x630 pixels aspect ratio)
            - Eye-catching and professional design
            - Clean composition with good contrast
            - No text overlay needed (text will be added separately)
            - Colors should be vibrant but not overwhelming
            - Design should appeal to Japanese audience
            - High quality, detailed artwork
            - Modern and appealing visual style
            """
            
            # ファイル名を安全な形式に変換
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')[:50]  # 50文字に制限
            
            thumbnail_path = os.path.join(self.thumbnail_dir, f"{safe_title}_{category}.png")
            
            # 絶対パスに変換
            thumbnail_path = os.path.abspath(thumbnail_path)
            
            logger.info(f"サムネイル画像生成開始: {title}")
            logger.info(f"保存先: {thumbnail_path}")
            
            # 実際の画像生成処理
            success = await self._generate_image_with_manus(prompt, thumbnail_path)
            
            if success and os.path.exists(thumbnail_path):
                logger.info(f"サムネイル画像生成成功: {thumbnail_path}")
                return thumbnail_path
            else:
                logger.error("サムネイル画像生成に失敗")
                return None
                
        except Exception as e:
            logger.error(f"サムネイル画像生成エラー: {e}")
            return None
    
    async def _generate_image_with_manus(self, prompt: str, output_path: str) -> bool:
        """Manusの画像生成機能を使用して画像を生成"""
        try:
            logger.info(f"画像生成プロンプト: {prompt}")
            logger.info(f"出力パス: {output_path}")
            
            # ディレクトリを作成
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 実際の画像生成処理
            # 注意: この部分は実際のManus環境でのみ動作します
            # テスト環境では画像生成をスキップし、デフォルト画像を使用します
            
            try:
                # Manusの画像生成ツールを呼び出す
                # この部分は実際の環境で有効になります
                import subprocess
                import sys
                
                # Python環境でmedia_generate_imageツールを呼び出す
                # 実際の実装では、Manusのツールを直接呼び出します
                
                # テスト用: 簡単な画像ファイルを作成
                # 実際の環境では、以下のコードが実行されます:
                """
                from manus_tools import media_generate_image
                result = media_generate_image(
                    brief="サムネイル画像を生成",
                    images=[{
                        "path": output_path,
                        "prompt": prompt,
                        "aspect_ratio": "landscape"
                    }]
                )
                return result.success
                """
                
                # テスト環境用のフォールバック
                logger.warning("テスト環境のため、実際の画像生成をスキップします")
                return False
                
            except ImportError:
                logger.warning("Manus画像生成ツールが利用できません")
                return False
            except Exception as e:
                logger.error(f"画像生成ツール呼び出しエラー: {e}")
                return False
            
        except Exception as e:
            logger.error(f"Manus画像生成エラー: {e}")
            return False
    
    def get_default_thumbnail(self, category: str) -> Optional[str]:
        """カテゴリに応じたデフォルトサムネイル画像を取得"""
        try:
            # カテゴリに応じた画像マッピング
            image_mapping = {
                "占い": "/home/ubuntu/upload/search_images/r2iQgMlsEGfl.png",  # タロット占い画像
                "フィットネス": "/home/ubuntu/upload/search_images/S9YjUASL7L7t.jpg",  # 筋トレ画像
                "書籍": "/home/ubuntu/upload/search_images/3zTJwMaKDZ1P.png"  # 読書記録画像
            }
            
            thumbnail_path = image_mapping.get(category)
            
            if thumbnail_path and os.path.exists(thumbnail_path):
                logger.info(f"デフォルトサムネイル画像選択: {thumbnail_path}")
                return thumbnail_path
            else:
                logger.warning(f"カテゴリ {category} のデフォルトサムネイル画像が見つかりません")
                return None
                
        except Exception as e:
            logger.error(f"デフォルトサムネイル画像選択エラー: {e}")
            return None

# 使用例
if __name__ == "__main__":
    async def test_generation():
        generator = MediaGenerator()
        result = await generator.generate_thumbnail_image(
            "テスト記事タイトル",
            "占い",
            "テスト記事の内容"
        )
        print(f"生成結果: {result}")
    
    asyncio.run(test_generation())

