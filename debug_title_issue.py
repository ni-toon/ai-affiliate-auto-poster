#!/usr/bin/env python3
"""
タイトルにアフィリエイトURLが入力される問題のデバッグ
"""

import asyncio
import logging
from modules.note_poster import NotePoster
import json

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_title_issue():
    """タイトル入力問題のデバッグ"""
    
    # 設定読み込み
    with open('config/config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    logger.info("=== タイトル入力問題のデバッグ開始 ===")
    
    # テスト用データ
    test_title = "テスト記事のタイトル"
    test_content = """# テスト記事

これはテスト用の記事です。

▼ テスト商品 - [Amazon商品リンク_テスト商品]

記事の内容をここに書きます。"""
    
    test_products = [
        {
            'name': 'テスト商品',
            'amazon_link': 'https://www.amazon.co.jp/dp/TEST123?tag=ninomono3-22'
        }
    ]
    
    note_poster = NotePoster(
        username=config['note']['username'],
        password=config['note']['password'],
        headless=True  # ヘッドレスモードでデバッグ
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
        await note_poster.page.goto('https://note.com/new')
        await note_poster.page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        
        logger.info("=== ページ構造の確認 ===")
        
        # ページ内のtextareaとinput要素を全て確認
        elements_info = await note_poster.page.evaluate("""
        () => {
            const textareas = Array.from(document.querySelectorAll('textarea'));
            const inputs = Array.from(document.querySelectorAll('input'));
            
            const info = {
                textareas: textareas.map((el, index) => ({
                    index: index,
                    placeholder: el.placeholder || '',
                    value: el.value || '',
                    id: el.id || '',
                    className: el.className || '',
                    name: el.name || ''
                })),
                inputs: inputs.map((el, index) => ({
                    index: index,
                    type: el.type || '',
                    placeholder: el.placeholder || '',
                    value: el.value || '',
                    id: el.id || '',
                    className: el.className || '',
                    name: el.name || ''
                }))
            };
            
            return info;
        }
        """)
        
        logger.info("=== TEXTAREA要素 ===")
        for i, textarea in enumerate(elements_info['textareas']):
            logger.info(f"Textarea {i}: placeholder='{textarea['placeholder']}', id='{textarea['id']}', class='{textarea['className']}'")
        
        logger.info("=== INPUT要素 ===")
        for i, input_el in enumerate(elements_info['inputs']):
            logger.info(f"Input {i}: type='{input_el['type']}', placeholder='{input_el['placeholder']}', id='{input_el['id']}', class='{input_el['className']}'")
        
        # タイトル入力のテスト
        logger.info("=== タイトル入力テスト ===")
        
        # 最初のtextareaにタイトルを入力
        if elements_info['textareas']:
            try:
                await note_poster.page.fill('textarea', test_title)
                logger.info(f"✅ タイトル入力成功: {test_title}")
                
                # 入力後の値を確認
                actual_value = await note_poster.page.evaluate('document.querySelector("textarea").value')
                logger.info(f"実際に入力された値: '{actual_value}'")
                
                if actual_value != test_title:
                    logger.warning(f"⚠️ 期待値と異なる値が入力されました")
                    logger.warning(f"期待値: '{test_title}'")
                    logger.warning(f"実際値: '{actual_value}'")
                
            except Exception as e:
                logger.error(f"❌ タイトル入力失敗: {e}")
        
        # 本文入力のテスト
        logger.info("=== 本文入力テスト ===")
        
        try:
            # 本文エリアをクリック
            await note_poster.page.click('div[contenteditable="true"]')
            await asyncio.sleep(1)
            
            # 本文を入力
            await note_poster.page.fill('div[contenteditable="true"]', test_content)
            logger.info("✅ 本文入力成功")
            
            # 入力後の内容を確認
            actual_content = await note_poster.page.evaluate('document.querySelector("div[contenteditable=\\"true\\"]").textContent')
            logger.info(f"実際に入力された本文（最初の100文字）: '{actual_content[:100]}...'")
            
        except Exception as e:
            logger.error(f"❌ 本文入力失敗: {e}")
        
        # 5秒間待機してユーザーが確認できるようにする
        logger.info("=== 5秒間待機（確認用） ===")
        await asyncio.sleep(5)
        
        logger.info("=== デバッグ完了 ===")
        
    except Exception as e:
        logger.error(f"デバッグ中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await note_poster.close_browser()

if __name__ == "__main__":
    asyncio.run(debug_title_issue())

