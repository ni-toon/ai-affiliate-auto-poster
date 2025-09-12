#!/usr/bin/env python3
"""
修正されたアフィリエイトリンク置換機能のテスト
"""

import asyncio
import logging
from modules.note_poster import NotePoster
import json

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_fixed_link_replacement():
    """修正されたリンク置換機能のテスト"""
    
    # 設定読み込み
    with open('config/config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    logger.info("=== 修正されたリンク置換機能のテスト開始 ===")
    
    # テスト用の記事データ
    test_article = {
        'title': '修正版リンク置換テスト記事',
        'content': '''# 修正版リンク置換テスト

これは修正されたアフィリエイトリンク置換機能のテストです。

▼ テスト商品1 - [Amazon商品リンク_テスト商品1]

この商品は素晴らしいです。詳細はリンクをご確認ください。

▼ テスト商品2 - [Amazon商品リンク_テスト商品2]

こちらもおすすめの商品です。

## まとめ

修正されたリンク置換機能により、プレースホルダーが正しくリンクに変換されることを確認します。''',
        'tags': ['#テスト', '#修正版', '#アフィリエイト'],
        'category': 'テスト'
    }
    
    # テスト用の商品データ
    test_products = [
        {
            'name': 'テスト商品1',
            'amazon_link': 'https://www.amazon.co.jp/dp/TEST001?tag=ninomono3-22',
            'category': 'テスト',
            'price_range': '1000-2000'
        },
        {
            'name': 'テスト商品2', 
            'amazon_link': 'https://www.amazon.co.jp/dp/TEST002?tag=ninomono3-22',
            'category': 'テスト',
            'price_range': '2000-3000'
        }
    ]
    
    note_poster = NotePoster(
        username=config['note']['username'],
        password=config['note']['password'],
        headless=True  # ヘッドレスモードでテスト
    )
    
    try:
        await note_poster.start_browser()
        
        # ログイン
        login_success = await note_poster.login()
        if not login_success:
            logger.error("❌ ログインに失敗")
            return
        
        logger.info("✅ ログイン成功")
        
        # 新規記事作成ページに移動
        await note_poster.page.goto('https://editor.note.com/notes/new')
        await note_poster.page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        
        # タイトル入力
        title_selectors = [
            'input[placeholder="記事タイトル"]',
            'textarea[placeholder="記事タイトル"]',
            'input[aria-label="記事タイトル"]',
            'textarea'
        ]
        
        title_input_success = False
        for selector in title_selectors:
            try:
                await note_poster.page.fill(selector, test_article['title'], timeout=5000)
                title_input_success = True
                logger.info(f"✅ タイトル入力成功: {selector}")
                break
            except:
                continue
        
        if not title_input_success:
            logger.error("❌ タイトル入力に失敗")
            return
        
        # 本文入力
        await note_poster.page.click('div[contenteditable="true"]')
        await note_poster.page.fill('div[contenteditable="true"]', test_article['content'])
        logger.info("✅ 本文入力成功")
        
        await asyncio.sleep(2)
        
        # 修正されたリンク置換機能をテスト
        logger.info("=== 修正されたリンク置換機能のテスト ===")
        
        conversion_success = await note_poster.convert_affiliate_placeholders(test_products)
        
        if conversion_success:
            logger.info("✅ リンク置換機能テスト成功")
            
            # 結果確認のため本文内容を取得
            content_after = await note_poster.page.evaluate(
                'document.querySelector("div[contenteditable=\\"true\\"]").innerHTML'
            )
            
            logger.info("=== 置換後の本文内容 ===")
            logger.info(content_after)
            
            # リンクが正しく作成されているかチェック
            link_count = await note_poster.page.evaluate(
                'document.querySelector("div[contenteditable=\\"true\\"]").querySelectorAll("a").length'
            )
            
            logger.info(f"作成されたリンク数: {link_count}")
            
            if link_count >= len(test_products):
                logger.info("✅ 期待されるリンク数が作成されました")
            else:
                logger.warning(f"⚠️ 期待されるリンク数({len(test_products)})より少ないリンクが作成されました({link_count})")
            
        else:
            logger.error("❌ リンク置換機能テスト失敗")
        
        # 下書き保存
        try:
            await note_poster.page.click('button:has-text("下書き保存")')
            await asyncio.sleep(2)
            logger.info("✅ 下書き保存成功")
        except Exception as e:
            logger.warning(f"下書き保存に失敗: {e}")
        
        logger.info("=== テスト完了 ===")
        
    except Exception as e:
        logger.error(f"テスト中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await note_poster.close_browser()

if __name__ == "__main__":
    asyncio.run(test_fixed_link_replacement())

