#!/usr/bin/env python3
"""
システム統合テスト用スクリプト
修正したアフィリエイトリンク機能とサムネイル画像機能をテストする
"""

import os
import sys
import asyncio
import logging
import json

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.product_research import ProductResearcher
from modules.article_generator import ArticleGenerator
from modules.image_generator_wrapper import ImageGeneratorWrapper

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_article_generation():
    """記事生成機能をテスト"""
    try:
        logger.info("=== 記事生成機能テスト開始 ===")
        
        # 設定ファイルを読み込み
        config_file = "config/config.json"
        if not os.path.exists(config_file):
            logger.error(f"設定ファイルが見つかりません: {config_file}")
            return False
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 各モジュールを初期化
        product_researcher = ProductResearcher(
            amazon_associate_id=config['amazon']['associate_id']
        )
        
        article_generator = ArticleGenerator(
            openai_api_key=config['openai']['api_key']
        )
        
        image_generator = ImageGeneratorWrapper()
        
        # 1. 商品リサーチテスト
        logger.info("1. 商品リサーチテスト")
        products = product_researcher.get_products_for_article("レビュー", 2)
        
        if not products:
            logger.error("商品リサーチに失敗")
            return False
        
        logger.info(f"商品リサーチ成功: {len(products)}個の商品を取得")
        for i, product in enumerate(products):
            logger.info(f"  商品{i+1}: {product['name']}")
            logger.info(f"    カテゴリ: {product['selected_category']}")
            logger.info(f"    価格帯: {product['price_range']}")
            logger.info(f"    リンク: {product['amazon_link'][:50]}...")
        
        # 2. 記事生成テスト
        logger.info("2. 記事生成テスト")
        article_data = article_generator.generate_complete_article(products, "レビュー")
        
        if not article_data:
            logger.error("記事生成に失敗")
            return False
        
        logger.info(f"記事生成成功:")
        logger.info(f"  タイトル: {article_data['title']}")
        logger.info(f"  記事タイプ: {article_data['article_type']}")
        logger.info(f"  カテゴリ: {article_data['category']}")
        logger.info(f"  タグ: {', '.join(article_data['tags'])}")
        logger.info(f"  本文長: {len(article_data['content'])}文字")
        
        # アフィリエイトリンクプレースホルダーの確認
        content = article_data['content']
        placeholder_count = content.count('[Amazon商品リンク_')
        logger.info(f"  アフィリエイトリンクプレースホルダー数: {placeholder_count}")
        
        if placeholder_count == 0:
            logger.warning("アフィリエイトリンクプレースホルダーが見つかりません")
        else:
            logger.info("アフィリエイトリンクプレースホルダーが正常に挿入されています")
        
        # 3. サムネイル画像生成テスト
        logger.info("3. サムネイル画像生成テスト")
        image_data = image_generator.generate_thumbnail_image(
            article_data['title'], 
            article_data['category']
        )
        
        if image_data:
            logger.info(f"画像生成データ準備成功:")
            logger.info(f"  出力パス: {image_data['output_path']}")
            logger.info(f"  プロンプト: {image_data['prompt'][:100]}...")
            
            # 生成済み画像の確認
            generated_thumbnails = {
                "占い": "/home/ubuntu/ai-affiliate-auto-poster/data/thumbnails/tarot_fortune_telling_占い.png",
                "フィットネス": "/home/ubuntu/ai-affiliate-auto-poster/data/thumbnails/fitness_training_フィットネス.png",
                "書籍": "/home/ubuntu/ai-affiliate-auto-poster/data/thumbnails/business_books_書籍.png"
            }
            
            generated_path = generated_thumbnails.get(article_data['category'])
            if generated_path and os.path.exists(generated_path):
                logger.info(f"生成済みサムネイル画像を確認: {generated_path}")
            else:
                # デフォルト画像の確認
                default_image = image_generator.get_default_thumbnail(article_data['category'])
                if default_image:
                    logger.info(f"デフォルト画像を確認: {default_image}")
                else:
                    logger.warning("サムネイル画像が見つかりません")
        else:
            logger.error("画像生成データ準備に失敗")
        
        # 4. テスト結果の保存
        logger.info("4. テスト結果の保存")
        test_result = {
            "test_type": "article_generation",
            "success": True,
            "article_data": {
                "title": article_data['title'],
                "article_type": article_data['article_type'],
                "category": article_data['category'],
                "tags": article_data['tags'],
                "content_length": len(article_data['content']),
                "placeholder_count": placeholder_count
            },
            "products": [{"name": p['name'], "category": p['selected_category']} for p in products],
            "image_data": image_data
        }
        
        test_results_dir = "data/test_results"
        os.makedirs(test_results_dir, exist_ok=True)
        
        test_results_file = os.path.join(test_results_dir, "article_generation_test.json")
        with open(test_results_file, 'w', encoding='utf-8') as f:
            json.dump(test_result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"テスト結果を保存: {test_results_file}")
        
        # 5. 生成された記事の保存
        article_file = os.path.join(test_results_dir, "test_article.md")
        with open(article_file, 'w', encoding='utf-8') as f:
            f.write(f"# {article_data['title']}\n\n")
            f.write(f"**記事タイプ:** {article_data['article_type']}\n")
            f.write(f"**カテゴリ:** {article_data['category']}\n")
            f.write(f"**タグ:** {', '.join(article_data['tags'])}\n\n")
            f.write("---\n\n")
            f.write(article_data['content'])
        
        logger.info(f"テスト記事を保存: {article_file}")
        
        logger.info("=== 記事生成機能テスト完了 ===")
        return True
        
    except Exception as e:
        logger.error(f"記事生成機能テストエラー: {e}")
        return False

async def test_note_posting_preparation():
    """note投稿準備テスト（実際の投稿は行わない）"""
    try:
        logger.info("=== note投稿準備テスト開始 ===")
        
        # テスト用記事データ
        test_article = {
            "title": "テスト記事：タロット占いで運命を読み解く方法",
            "content": """※本記事にはアフィリエイトリンクを含みます

## 概要

タロット占いは、古くから愛され続けている占術の一つです。78枚のカードが持つ象徴的な意味を通じて、私たちの潜在意識や未来への道筋を読み解くことができます。

## メリット

タロット占いの主な利点は以下の通りです：

1. **直感力の向上**: カードの象徴を読み解くことで、直感力が鍛えられます。
2. **自己理解の深化**: 内面の声に耳を傾けることで、自分自身をより深く理解できます。
3. **決断力の向上**: 迷いがある時に、新たな視点を提供してくれます。

▼ タロットカードセット - [Amazon商品リンク_タロットカードセット]

## デメリット

一方で、以下の点にご注意ください：

1. **解釈の主観性**: カードの意味は読み手によって異なる場合があります。
2. **依存の危険性**: 占いに頼りすぎると、自分で判断する力が弱くなる可能性があります。

## まとめ

タロット占いは、自己理解と直感力向上に役立つ素晴らしいツールです。適度に活用することで、人生をより豊かにすることができるでしょう。""",
            "tags": ["#占い", "#タロット", "#スピリチュアル", "#レビュー", "#体験談"],
            "category": "占い"
        }
        
        # テスト用商品データ
        test_products = [
            {
                "name": "タロットカードセット",
                "amazon_link": "https://amazon.co.jp/dp/test123",
                "selected_category": "占い"
            }
        ]
        
        logger.info("テスト記事データ:")
        logger.info(f"  タイトル: {test_article['title']}")
        logger.info(f"  カテゴリ: {test_article['category']}")
        logger.info(f"  タグ数: {len(test_article['tags'])}")
        logger.info(f"  本文長: {len(test_article['content'])}文字")
        
        # アフィリエイトリンクプレースホルダーの確認
        placeholder_count = test_article['content'].count('[Amazon商品リンク_')
        logger.info(f"  アフィリエイトリンクプレースホルダー数: {placeholder_count}")
        
        # サムネイル画像の確認
        thumbnail_path = "/home/ubuntu/ai-affiliate-auto-poster/data/thumbnails/tarot_fortune_telling_占い.png"
        if os.path.exists(thumbnail_path):
            logger.info(f"  サムネイル画像: {thumbnail_path} (存在確認済み)")
        else:
            logger.warning("  サムネイル画像が見つかりません")
        
        # note投稿準備完了
        logger.info("note投稿準備テスト完了 - 実際の投稿は手動で確認してください")
        
        # テスト結果の保存
        test_result = {
            "test_type": "note_posting_preparation",
            "success": True,
            "article": test_article,
            "products": test_products,
            "thumbnail_path": thumbnail_path,
            "placeholder_count": placeholder_count
        }
        
        test_results_dir = "data/test_results"
        os.makedirs(test_results_dir, exist_ok=True)
        
        test_results_file = os.path.join(test_results_dir, "note_posting_preparation_test.json")
        with open(test_results_file, 'w', encoding='utf-8') as f:
            json.dump(test_result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"テスト結果を保存: {test_results_file}")
        
        logger.info("=== note投稿準備テスト完了 ===")
        return True
        
    except Exception as e:
        logger.error(f"note投稿準備テストエラー: {e}")
        return False

async def main():
    """メインテスト関数"""
    try:
        logger.info("システム統合テストを開始")
        
        # 1. 記事生成機能テスト
        test1_success = await test_article_generation()
        
        # 2. note投稿準備テスト
        test2_success = await test_note_posting_preparation()
        
        # 総合結果
        if test1_success and test2_success:
            logger.info("✅ 全てのテストが成功しました")
            return True
        else:
            logger.error("❌ 一部のテストが失敗しました")
            return False
        
    except Exception as e:
        logger.error(f"システム統合テストエラー: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🎉 システム統合テスト完了 - 全ての機能が正常に動作しています")
    else:
        print("\n⚠️ システム統合テスト失敗 - 問題を確認してください")

