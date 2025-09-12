#!/usr/bin/env python3
"""
アフィリエイトリンク置換処理のデバッグ用スクリプト
"""

import asyncio
import logging
from modules.note_poster import NotePoster
from modules.product_research import ProductResearcher
import json

# ログ設定
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_link_replacement():
    """リンク置換処理のデバッグ"""
    
    # 設定読み込み
    with open('config/config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # テスト用の記事データ
    test_article = {
        'title': 'テスト記事：アフィリエイトリンク置換確認',
        'content': '''# テスト記事

これはアフィリエイトリンクの置換テストです。

▼ テスト商品1 - [Amazon商品リンク_テスト商品1]

この商品は素晴らしいです。

▼ テスト商品2 - [Amazon商品リンク_テスト商品2]

こちらもおすすめです。

## まとめ

以上、テスト記事でした。''',
        'tags': ['#テスト', '#デバッグ'],
        'category': 'テスト'
    }
    
    # テスト用の商品データ
    test_products = [
        {
            'name': 'テスト商品1',
            'amazon_url': 'https://www.amazon.co.jp/dp/TEST001?tag=ninomono3-22',
            'category': 'テスト',
            'price_range': '1000-2000'
        },
        {
            'name': 'テスト商品2', 
            'amazon_url': 'https://www.amazon.co.jp/dp/TEST002?tag=ninomono3-22',
            'category': 'テスト',
            'price_range': '2000-3000'
        }
    ]
    
    logger.info("=== アフィリエイトリンク置換デバッグ開始 ===")
    
    # 1. プレースホルダーの検出テスト
    logger.info("1. プレースホルダー検出テスト")
    content = test_article['content']
    
    for product in test_products:
        placeholder = f"[Amazon商品リンク_{product['name']}]"
        if placeholder in content:
            logger.info(f"✅ プレースホルダー検出成功: {placeholder}")
        else:
            logger.error(f"❌ プレースホルダー検出失敗: {placeholder}")
    
    # 2. note投稿プロセスのテスト
    logger.info("2. note投稿プロセステスト")
    
    note_poster = NotePoster(
        username=config['note']['username'],
        password=config['note']['password'],
        headless=False  # デバッグのため表示モード
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
        title_selector = 'input[placeholder="記事タイトル"], input[aria-label="記事タイトル"]'
        await note_poster.page.fill(title_selector, test_article['title'])
        logger.info("✅ タイトル入力成功")
        
        # 本文入力
        content_selector = 'div[contenteditable="true"]'
        await note_poster.page.click(content_selector)
        await note_poster.page.fill(content_selector, test_article['content'])
        logger.info("✅ 本文入力成功")
        
        await asyncio.sleep(2)
        
        # 3. プレースホルダー検索テスト
        logger.info("3. プレースホルダー検索テスト")
        
        for product in test_products:
            placeholder = f"[Amazon商品リンク_{product['name']}]"
            logger.info(f"検索対象プレースホルダー: {placeholder}")
            
            # JavaScriptでプレースホルダーを検索
            js_code = f"""
            () => {{
                const contentDiv = document.querySelector('div[contenteditable="true"]');
                if (!contentDiv) {{
                    return {{ found: false, error: '本文エリアが見つかりません' }};
                }}
                
                const text = contentDiv.textContent || contentDiv.innerText;
                const found = text.includes('{placeholder}');
                
                return {{ 
                    found: found,
                    fullText: text,
                    placeholder: '{placeholder}'
                }};
            }}
            """
            
            result = await note_poster.page.evaluate(js_code)
            
            if result['found']:
                logger.info(f"✅ プレースホルダー検出成功: {placeholder}")
                
                # 4. テキスト選択テスト
                logger.info("4. テキスト選択テスト")
                
                select_js = f"""
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
                    return {{ success: false, error: 'テキストノードが見つかりません' }};
                }}
                """
                
                select_result = await note_poster.page.evaluate(select_js)
                
                if select_result['success']:
                    logger.info(f"✅ テキスト選択成功: {select_result['selectedText']}")
                    
                    # 5. リンクボタン検索テスト
                    logger.info("5. リンクボタン検索テスト")
                    
                    link_selectors = [
                        'button[aria-label="リンク"]',
                        'button[title="リンク"]',
                        'button:has([data-icon="link"])',
                        '[data-testid="link-button"]',
                        'button[data-tooltip="リンク"]'
                    ]
                    
                    link_found = False
                    for selector in link_selectors:
                        try:
                            element = await note_poster.page.query_selector(selector)
                            if element:
                                logger.info(f"✅ リンクボタン発見: {selector}")
                                link_found = True
                                
                                # ボタンをクリックしてみる
                                await note_poster.page.click(selector)
                                await asyncio.sleep(2)
                                
                                # URL入力ダイアログの確認
                                url_selectors = [
                                    'input[placeholder*="URL"]',
                                    'input[type="url"]',
                                    'input[name="url"]',
                                    'input[aria-label*="URL"]'
                                ]
                                
                                url_input_found = False
                                for url_selector in url_selectors:
                                    try:
                                        url_element = await note_poster.page.query_selector(url_selector)
                                        if url_element:
                                            logger.info(f"✅ URL入力フィールド発見: {url_selector}")
                                            url_input_found = True
                                            
                                            # テストURLを入力
                                            await note_poster.page.fill(url_selector, product['amazon_url'])
                                            logger.info(f"✅ URL入力成功: {product['amazon_url']}")
                                            
                                            # 適用ボタンを探す
                                            apply_selectors = [
                                                'button:has-text("適用")',
                                                'button:has-text("OK")',
                                                'button:has-text("確定")',
                                                'button[type="submit"]'
                                            ]
                                            
                                            for apply_selector in apply_selectors:
                                                try:
                                                    apply_element = await note_poster.page.query_selector(apply_selector)
                                                    if apply_element:
                                                        logger.info(f"✅ 適用ボタン発見: {apply_selector}")
                                                        await note_poster.page.click(apply_selector)
                                                        await asyncio.sleep(2)
                                                        logger.info("✅ リンク適用完了")
                                                        break
                                                except Exception as e:
                                                    logger.debug(f"適用ボタンクリック失敗: {apply_selector} - {e}")
                                            
                                            break
                                    except Exception as e:
                                        logger.debug(f"URL入力フィールド確認失敗: {url_selector} - {e}")
                                
                                if not url_input_found:
                                    logger.error("❌ URL入力フィールドが見つかりません")
                                
                                break
                        except Exception as e:
                            logger.debug(f"リンクボタン確認失敗: {selector} - {e}")
                    
                    if not link_found:
                        logger.error("❌ リンクボタンが見つかりません")
                        
                        # ページのHTML構造を確認
                        logger.info("ページのHTML構造を確認中...")
                        html_content = await note_poster.page.content()
                        
                        # ボタン要素を検索
                        buttons = await note_poster.page.query_selector_all('button')
                        logger.info(f"ページ内のボタン数: {len(buttons)}")
                        
                        for i, button in enumerate(buttons[:10]):  # 最初の10個のボタンを確認
                            try:
                                text = await button.text_content()
                                aria_label = await button.get_attribute('aria-label')
                                title = await button.get_attribute('title')
                                logger.info(f"ボタン{i}: text='{text}', aria-label='{aria_label}', title='{title}'")
                            except:
                                pass
                
                else:
                    logger.error(f"❌ テキスト選択失敗: {select_result.get('error', '不明なエラー')}")
            else:
                logger.error(f"❌ プレースホルダー検出失敗: {placeholder}")
                logger.info(f"実際のテキスト: {result['fullText'][:200]}...")
        
        # デバッグ完了後、ページを保持（手動確認用）
        logger.info("デバッグ完了。ブラウザを手動で確認してください。")
        input("Enterキーを押すとブラウザを閉じます...")
        
    except Exception as e:
        logger.error(f"デバッグ中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await note_poster.close_browser()

if __name__ == "__main__":
    asyncio.run(debug_link_replacement())

