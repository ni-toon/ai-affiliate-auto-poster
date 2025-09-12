#!/usr/bin/env python3
"""
サンプルサムネイル画像生成スクリプト
実際のManus画像生成機能を使用してサムネイル画像を生成する
"""

import os

def generate_sample_thumbnails():
    """サンプルサムネイル画像を生成"""
    
    # サムネイル保存ディレクトリを作成
    thumbnail_dir = "/home/ubuntu/ai-affiliate-auto-poster/data/thumbnails"
    os.makedirs(thumbnail_dir, exist_ok=True)
    
    # 生成する画像のデータ
    images_to_generate = [
        {
            "category": "占い",
            "title": "タロット占いで運命を読み解く方法",
            "prompt": """Create a professional thumbnail image for a Japanese blog article about 占い (fortune telling). 

Title: タロット占いで運命を読み解く方法

Style: mystical, spiritual, elegant
Visual elements: tarot cards, crystal ball, celestial symbols, purple and gold colors
Mood: mysterious and enchanting

Requirements:
- Size suitable for social media thumbnails (landscape aspect ratio)
- Eye-catching and professional design
- Clean composition with good contrast
- No text overlay needed (text will be added separately)
- Colors should be vibrant but not overwhelming
- Design should appeal to Japanese audience
- High quality, detailed artwork
- Modern and appealing visual style""",
            "filename": "tarot_fortune_telling_占い.png"
        },
        {
            "category": "フィットネス",
            "title": "筋トレ初心者のための効果的なトレーニング",
            "prompt": """Create a professional thumbnail image for a Japanese blog article about フィットネス (fitness). 

Title: 筋トレ初心者のための効果的なトレーニング

Style: energetic, modern, motivational
Visual elements: fitness equipment, dumbbells, yoga mat, healthy lifestyle
Mood: dynamic and inspiring

Requirements:
- Size suitable for social media thumbnails (landscape aspect ratio)
- Eye-catching and professional design
- Clean composition with good contrast
- No text overlay needed (text will be added separately)
- Colors should be vibrant but not overwhelming
- Design should appeal to Japanese audience
- High quality, detailed artwork
- Modern and appealing visual style""",
            "filename": "fitness_training_フィットネス.png"
        },
        {
            "category": "書籍",
            "title": "ビジネス書から学ぶ成功の秘訣",
            "prompt": """Create a professional thumbnail image for a Japanese blog article about 書籍 (books). 

Title: ビジネス書から学ぶ成功の秘訣

Style: intellectual, warm, professional
Visual elements: books, reading, library atmosphere, knowledge symbols
Mood: scholarly and inviting

Requirements:
- Size suitable for social media thumbnails (landscape aspect ratio)
- Eye-catching and professional design
- Clean composition with good contrast
- No text overlay needed (text will be added separately)
- Colors should be vibrant but not overwhelming
- Design should appeal to Japanese audience
- High quality, detailed artwork
- Modern and appealing visual style""",
            "filename": "business_books_書籍.png"
        }
    ]
    
    return images_to_generate, thumbnail_dir

if __name__ == "__main__":
    images, output_dir = generate_sample_thumbnails()
    print(f"画像生成データを準備しました。出力ディレクトリ: {output_dir}")
    for i, img in enumerate(images):
        print(f"{i+1}. {img['category']}: {img['filename']}")
        print(f"   プロンプト: {img['prompt'][:100]}...")
        print()

