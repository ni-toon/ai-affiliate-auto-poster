#!/usr/bin/env python3
"""
シンプルなアフィリエイトリンク置換テスト
"""

import asyncio
import logging
from playwright.async_api import async_playwright
import json

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def simple_link_test():
    """シンプルなリンク置換テスト"""
    
    # 設定読み込み
    with open('config/config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    logger.info("=== シンプルなリンク置換テスト開始 ===")
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()
    
    try:
        # noteにアクセス
        await page.goto('https://note.com/login')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        
        # ログイン
        await page.fill('input[type="email"]', config['note']['username'])
        await page.fill('input[type="password"]', config['note']['password'])
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        
        # 新規記事作成
        await page.goto('https://editor.note.com/notes/new')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        
        # タイトル入力
        await page.fill('input[placeholder="記事タイトル"]', 'リンク置換テスト記事')
        
        # 本文入力（プレースホルダー付き）
        test_content = """# リンク置換テスト

これはテスト記事です。

▼ テスト商品 - [Amazon商品リンク_テスト商品]

この商品をおすすめします。

## まとめ

以上です。"""
        
        await page.click('div[contenteditable="true"]')
        await page.fill('div[contenteditable="true"]', test_content)
        await asyncio.sleep(2)
        
        # プレースホルダーの存在確認
        content_text = await page.evaluate('document.querySelector("div[contenteditable=\\"true\\"]").textContent')
        placeholder = '[Amazon商品リンク_テスト商品]'
        
        if placeholder in content_text:
            logger.info(f"✅ プレースホルダー確認成功: {placeholder}")
            
            # プレースホルダーを選択
            select_result = await page.evaluate(f'''
            () => {{
                const contentDiv = document.querySelector('div[contenteditable="true"]');
                const walker = document.createTreeWalker(
                    contentDiv,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );
                
                let node;
                while (node = walker.nextNode()) {{
                    if (node.textContent.includes('{placeholder}')) {{
                        const range = document.createRange();
                        const selection = window.getSelection();
                        
                        const startIndex = node.textContent.indexOf('{placeholder}');
                        const endIndex = startIndex + '{placeholder}'.length;
                        
                        range.setStart(node, startIndex);
                        range.setEnd(node, endIndex);
                        selection.removeAllRanges();
                        selection.addRange(range);
                        
                        return {{ success: true, selectedText: selection.toString() }};
                    }}
                }}
                return {{ success: false }};
            }}
            ''')
            
            if select_result['success']:
                logger.info(f"✅ テキスト選択成功: {select_result['selectedText']}")
                
                # ページ内のすべてのボタンを確認
                buttons = await page.query_selector_all('button')
                logger.info(f"ページ内のボタン数: {len(buttons)}")
                
                # リンクボタンを探す
                link_button_found = False
                for i, button in enumerate(buttons):
                    try:
                        aria_label = await button.get_attribute('aria-label')
                        title = await button.get_attribute('title')
                        text = await button.text_content()
                        
                        if aria_label and 'リンク' in aria_label:
                            logger.info(f"✅ リンクボタン発見 (aria-label): {aria_label}")
                            link_button_found = True
                            
                            # ボタンをクリック
                            await button.click()
                            await asyncio.sleep(2)
                            
                            # URL入力ダイアログを確認
                            url_input = await page.query_selector('input[placeholder*="URL"], input[type="url"]')
                            if url_input:
                                logger.info("✅ URL入力フィールド発見")
                                
                                # テストURLを入力
                                test_url = 'https://www.amazon.co.jp/dp/TEST123?tag=ninomono3-22'
                                await url_input.fill(test_url)
                                logger.info(f"✅ URL入力完了: {test_url}")
                                
                                # 適用ボタンを探してクリック
                                apply_buttons = await page.query_selector_all('button')
                                for apply_button in apply_buttons:
                                    button_text = await apply_button.text_content()
                                    if button_text and ('適用' in button_text or 'OK' in button_text):
                                        logger.info(f"✅ 適用ボタン発見: {button_text}")
                                        await apply_button.click()
                                        await asyncio.sleep(2)
                                        logger.info("✅ リンク適用完了")
                                        break
                            else:
                                logger.error("❌ URL入力フィールドが見つかりません")
                            
                            break
                        elif title and 'リンク' in title:
                            logger.info(f"✅ リンクボタン発見 (title): {title}")
                            link_button_found = True
                            break
                        elif text and 'リンク' in text:
                            logger.info(f"✅ リンクボタン発見 (text): {text}")
                            link_button_found = True
                            break
                            
                    except Exception as e:
                        continue
                
                if not link_button_found:
                    logger.error("❌ リンクボタンが見つかりません")
                    
                    # ツールバーの詳細確認
                    logger.info("ツールバーの詳細確認...")
                    toolbar_buttons = await page.query_selector_all('[role="toolbar"] button, .toolbar button, [data-testid*="toolbar"] button')
                    for i, button in enumerate(toolbar_buttons[:20]):
                        try:
                            aria_label = await button.get_attribute('aria-label')
                            title = await button.get_attribute('title')
                            text = await button.text_content()
                            class_name = await button.get_attribute('class')
                            logger.info(f"ツールバーボタン{i}: aria-label='{aria_label}', title='{title}', text='{text}', class='{class_name}'")
                        except:
                            pass
            else:
                logger.error("❌ テキスト選択失敗")
        else:
            logger.error(f"❌ プレースホルダーが見つかりません: {placeholder}")
            logger.info(f"実際のテキスト: {content_text}")
        
        # テスト完了
        logger.info("テスト完了")
        
    except Exception as e:
        logger.error(f"テスト中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(simple_link_test())

