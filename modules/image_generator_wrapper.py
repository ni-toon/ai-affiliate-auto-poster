"""
画像生成ラッパーモジュール
Manusの画像生成機能を呼び出すためのラッパー
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ImageGeneratorWrapper:
    def __init__(self):
        self.thumbnail_dir = "data/thumbnails"
        os.makedirs(self.thumbnail_dir, exist_ok=True)
    
    def generate_thumbnail_image(self, title: str, category: str) -> Optional[str]:
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
            - Size suitable for social media thumbnails (landscape aspect ratio)
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
            logger.info(f"プロンプト: {prompt}")
            
            return {
                "prompt": prompt,
                "output_path": thumbnail_path,
                "category": category,
                "title": title
            }
                
        except Exception as e:
            logger.error(f"サムネイル画像生成準備エラー: {e}")
            return None
    
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

