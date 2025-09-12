#!/usr/bin/env python3
"""
記事生成から投稿までの完全なフローをデバッグ
"""

import asyncio
import logging
import json
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.product_research import ProductResearcher
from modules.article_generator import ArticleGenerator
from modules.note_poster import NotePoster

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_full_flow():
    """完全なフローのデバッグ"""
    
    logger.info("=== 完全フローデバッグ開始 ===")
    
    try:
        # 設定読み込み
        with open('config/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 1. 商品リサーチ
        logger.info("=== 1. 商品リサーチ ===")
        researcher = ProductResearcher(config['amazon']['associate_id'])
        products = researcher.get_products_for_article('レビュー', 2)
        
        logger.info(f"取得した商品数: {len(products)}")
        for i, product in enumerate(products):
            logger.info(f"商品{i+1}: {product['name']}")
            logger.info(f"  URL: {product['amazon_link']}")
        
        # 2. 記事生成
        logger.info("=== 2. 記事生成 ===")
        generator = ArticleGenerator(config['openai']['api_key'])
        article_data = generator.generate_complete_article(products, 'レビュー')
        
        logger.info(f"生成されたタイトル: {article_data['title']}")
        logger.info(f"記事カテゴリ: {article_data['category']}")
        logger.info(f"タグ: {', '.join(article_data['tags'])}")
        
        # プレースホルダーの確認
        import re
        placeholders = re.findall(r'\\[Amazon商品リンク_[^\\]]+\\]', article_data['content'])
        logger.info(f"プレースホルダー数: {len(placeholders)}")
        for placeholder in placeholders:
            logger.info(f"  - {placeholder}")
        
        # 3. note投稿のシミュレーション（実際には投稿しない）
        logger.info("=== 3. note投稿シミュレーション ===")
        
        note_poster = NotePoster(
            username=config['note']['username'],
            password=config['note']['password'],
            headless=True
        )
        
        await note_poster.start_browser()
        
        # ログイン
        login_success = await note_poster.login()
        if not login_success:
            logger.error("❌ ログインに失敗")
            return
        
        logger.info("✅ ログイン成功")
        
        # 新規記事作成ページに移動
        await note_poster.page.goto('https://note.com/new')
        await note_poster.page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        
        # タイトル入力のテスト
        logger.info("=== タイトル入力テスト ===")
        try:
            await note_poster.page.fill('textarea[placeholder="記事タイトル"]', article_data['title'])
            
            # 入力後の値を確認
            actual_title = await note_poster.page.evaluate('document.querySelector("textarea[placeholder=\\"記事タイトル\\"]").value')
            logger.info(f"入力されたタイトル: '{actual_title}'")
            
            if actual_title == article_data['title']:
                logger.info("✅ タイトル入力正常")
            else:
                logger.error(f"❌ タイトル入力異常 - 期待値: '{article_data['title']}', 実際値: '{actual_title}'")
                
        except Exception as e:
            logger.error(f"❌ タイトル入力エラー: {e}")
        
        # 本文入力のテスト
        logger.info("=== 本文入力テスト ===")
        try:
            # 本文エリアをクリック
            await note_poster.page.click('div[contenteditable="true"]')
            await asyncio.sleep(1)
            
            # 本文を入力（プレーンテキストとして）
            await note_poster.page.fill('div[contenteditable="true"]', article_data['content'])
            
            # 入力後の内容を確認
            actual_content = await note_poster.page.evaluate('document.querySelector("div[contenteditable=\\"true\\"]").textContent')
            logger.info(f"入力された本文（最初の200文字）: '{actual_content[:200]}...'")
            
            # プレースホルダーが含まれているかチェック
            if '[Amazon商品リンク_' in actual_content:
                logger.info("✅ プレースホルダーが本文に含まれています")
            else:
                logger.warning("⚠️ プレースホルダーが本文に見つかりません")
                
        except Exception as e:
            logger.error(f"❌ 本文入力エラー: {e}")
        
        # アフィリエイトリンク変換のテスト
        logger.info("=== アフィリエイトリンク変換テスト ===")
        try:
            # convert_affiliate_placeholders メソッドを呼び出し
            await note_poster.convert_affiliate_placeholders(products)
            logger.info("✅ アフィリエイトリンク変換処理完了")
            
            # 変換後の内容を確認
            final_content = await note_poster.page.evaluate('document.querySelector("div[contenteditable=\\"true\\"]").innerHTML')
            
            # リンクが作成されているかチェック
            if '<a href=' in final_content:
                logger.info("✅ リンクが作成されました")
                # リンクの数を数える
                link_count = final_content.count('<a href=')
                logger.info(f"作成されたリンク数: {link_count}")
            else:
                logger.warning("⚠️ リンクが作成されていません")
                
        except Exception as e:
            logger.error(f"❌ アフィリエイトリンク変換エラー: {e}")
        
        logger.info("=== デバッグ完了 ===")
        
    except Exception as e:
        logger.error(f"デバッグ中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            await note_poster.close_browser()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(debug_full_flow())

