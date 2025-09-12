#!/usr/bin/env python3
"""
詳細なリンク作成デバッグスクリプト
アフィリエイトリンクが正しく作成されない問題を詳細に分析
"""

import asyncio
import logging
import sys
import os
import json

# プロジェクトルートをパスに追加
sys.path.append('/home/ubuntu/ai-affiliate-auto-poster')

from modules.note_poster import NotePoster
from modules.product_research import ProductResearcher
from modules.article_generator import ArticleGenerator

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def debug_link_creation():
    """リンク作成の詳細デバッグ"""
    
    logger.info("=== 詳細リンク作成デバッグ開始 ===")
    
    # 設定読み込み
    config_path = '/home/ubuntu/ai-affiliate-auto-poster/config/config.json'
    
    try:
        # 設定読み込み
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # NotePosterを初期化
        note_poster = NotePoster(
            username=config['note']['username'],
            password=config['note']['password'],
            headless=True
        )
        
        # ブラウザを起動
        await note_poster.start_browser()
        
        # noteにログイン
        logger.info("=== 1. noteログイン ===")
        login_success = await note_poster.login()
        if not login_success:
            logger.error("ログインに失敗しました")
            return
        logger.info("✅ ログイン成功")
        
        # 投稿ページに移動
        logger.info("=== 2. 投稿ページに移動 ===")
        await note_poster.page.goto('https://note.com/n/n8b8b8b8b8b8b/edit', wait_until='networkidle')
        await asyncio.sleep(2)
        
        # テスト用のタイトルと本文を入力
        logger.info("=== 3. テスト記事の入力 ===")
        test_title = "アフィリエイトリンクテスト記事"
        test_content = """※本記事にはアフィリエイトリンクを含みます

## テスト商品の紹介

この商品は非常におすすめです。

▼ テスト商品 - [Amazon商品リンク_テスト商品]

詳細な説明がここに入ります。

## まとめ

[Amazon商品リンク_テスト商品] は素晴らしい商品です。"""
        
        # タイトル入力
        try:
            await note_poster.page.fill('input[placeholder*="タイトル"]', test_title)
            logger.info(f"✅ タイトル入力成功: {test_title}")
        except Exception as e:
            logger.error(f"❌ タイトル入力失敗: {e}")
            return
        
        # 本文入力
        try:
            await note_poster.page.fill('div[contenteditable="true"]', test_content)
            logger.info("✅ 本文入力成功")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"❌ 本文入力失敗: {e}")
            return
        
        # 本文の内容を確認
        content_check = await note_poster.page.evaluate("""
        () => {
            const contentDiv = document.querySelector('div[contenteditable="true"]');
            return contentDiv ? contentDiv.textContent : null;
        }
        """)
        logger.info(f"入力された本文の確認: {content_check[:100]}...")
        
        # プレースホルダーの存在確認
        placeholder_check = await note_poster.page.evaluate("""
        () => {
            const contentDiv = document.querySelector('div[contenteditable="true"]');
            if (!contentDiv) return { found: false, error: '本文エリアが見つかりません' };
            
            const text = contentDiv.textContent;
            const placeholder = '[Amazon商品リンク_テスト商品]';
            const found = text.includes(placeholder);
            
            return { 
                found: found, 
                text: text,
                placeholder: placeholder,
                count: (text.match(new RegExp(placeholder.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&'), 'g')) || []).length
            };
        }
        """)
        
        logger.info(f"プレースホルダー確認: {placeholder_check}")
        
        if not placeholder_check['found']:
            logger.error("❌ プレースホルダーが見つかりません")
            return
        
        logger.info(f"✅ プレースホルダー発見: {placeholder_check['count']}個")
        
        # テスト用商品データ
        test_products = [{
            'name': 'テスト商品',
            'amazon_link': 'https://www.amazon.co.jp/dp/TEST123?tag=ninomono3-22'
        }]
        
        # リンク変換処理を実行
        logger.info("=== 4. リンク変換処理開始 ===")
        
        # 詳細なステップバイステップ実行
        placeholder = "[Amazon商品リンク_テスト商品]"
        amazon_url = test_products[0]['amazon_link']
        
        logger.info(f"変換対象: {placeholder} → {amazon_url}")
        
        # ステップ1: プレースホルダーを選択
        logger.info("--- ステップ1: プレースホルダー選択 ---")
        selection_result = await note_poster.page.evaluate(f"""
        () => {{
            const contentDiv = document.querySelector('div[contenteditable="true"]');
            if (!contentDiv) {{
                return {{ success: false, error: '本文エリアが見つかりません' }};
            }}
            
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
                    
                    return {{ 
                        success: true, 
                        selectedText: selection.toString(),
                        nodeText: node.textContent,
                        startIndex: startIndex,
                        endIndex: endIndex
                    }};
                }}
            }}
            return {{ success: false, error: 'プレースホルダーが見つかりません' }};
        }}
        """)
        
        logger.info(f"選択結果: {selection_result}")
        
        if not selection_result['success']:
            logger.error(f"❌ プレースホルダー選択失敗: {selection_result['error']}")
            return
        
        logger.info("✅ プレースホルダー選択成功")
        await asyncio.sleep(1)
        
        # ステップ2: ツールバーの表示確認
        logger.info("--- ステップ2: ツールバー確認 ---")
        toolbar_check = await note_poster.page.evaluate("""
        () => {
            const linkButtons = document.querySelectorAll('button[aria-label="リンク"]');
            const toolbars = document.querySelectorAll('[role="toolbar"]');
            
            return {
                linkButtonCount: linkButtons.length,
                toolbarCount: toolbars.length,
                linkButtonVisible: Array.from(linkButtons).some(btn => btn.offsetParent !== null),
                linkButtonDetails: Array.from(linkButtons).map(btn => ({
                    visible: btn.offsetParent !== null,
                    disabled: btn.disabled,
                    ariaLabel: btn.getAttribute('aria-label'),
                    className: btn.className
                }))
            };
        }
        """)
        
        logger.info(f"ツールバー確認: {toolbar_check}")
        
        # ステップ3: リンクボタンクリック
        logger.info("--- ステップ3: リンクボタンクリック ---")
        
        # ページを上部にスクロール
        await note_poster.page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(0.5)
        
        # 本文エリアにフォーカス
        await note_poster.page.click('div[contenteditable="true"]')
        await asyncio.sleep(0.5)
        
        # プレースホルダーを再選択
        await note_poster.page.evaluate(f"""
        () => {{
            const contentDiv = document.querySelector('div[contenteditable="true"]');
            if (!contentDiv) return false;
            
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
                    
                    return true;
                }}
            }}
            return false;
        }}
        """)
        
        await asyncio.sleep(0.5)
        
        # リンクボタンを探してクリック
        link_button = await note_poster.page.query_selector('button[aria-label="リンク"]')
        if not link_button:
            logger.error("❌ リンクボタンが見つかりません")
            return
        
        # ボタンの詳細情報を取得
        button_info = await note_poster.page.evaluate("""
        (button) => {
            const rect = button.getBoundingClientRect();
            return {
                visible: button.offsetParent !== null,
                disabled: button.disabled,
                rect: {
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height
                },
                inViewport: rect.top >= 0 && rect.left >= 0 && 
                           rect.bottom <= window.innerHeight && 
                           rect.right <= window.innerWidth
            };
        }
        """, link_button)
        
        logger.info(f"リンクボタン情報: {button_info}")
        
        # 座標でクリック
        try:
            button_box = await link_button.bounding_box()
            if button_box:
                center_x = button_box['x'] + button_box['width'] / 2
                center_y = button_box['y'] + button_box['height'] / 2
                await note_poster.page.mouse.click(center_x, center_y)
                logger.info("✅ リンクボタンを座標でクリック成功")
            else:
                logger.error("❌ ボタンのbounding_boxが取得できません")
                return
        except Exception as e:
            logger.error(f"❌ リンクボタンクリック失敗: {e}")
            return
        
        # ダイアログの表示を待機
        await asyncio.sleep(2)
        
        # ステップ4: URL入力ダイアログの確認
        logger.info("--- ステップ4: URL入力ダイアログ確認 ---")
        dialog_check = await note_poster.page.evaluate("""
        () => {
            const textareas = document.querySelectorAll('textarea');
            const inputs = document.querySelectorAll('input[type="url"], input[type="text"]');
            const dialogs = document.querySelectorAll('[role="dialog"]');
            
            return {
                textareaCount: textareas.length,
                inputCount: inputs.length,
                dialogCount: dialogs.length,
                textareaVisible: Array.from(textareas).some(ta => ta.offsetParent !== null),
                inputVisible: Array.from(inputs).some(inp => inp.offsetParent !== null),
                allElements: {
                    textareas: Array.from(textareas).map(ta => ({
                        visible: ta.offsetParent !== null,
                        placeholder: ta.placeholder,
                        value: ta.value
                    })),
                    inputs: Array.from(inputs).map(inp => ({
                        visible: inp.offsetParent !== null,
                        type: inp.type,
                        placeholder: inp.placeholder,
                        value: inp.value
                    }))
                }
            };
        }
        """)
        
        logger.info(f"ダイアログ確認: {dialog_check}")
        
        # ステップ5: URL入力
        logger.info("--- ステップ5: URL入力 ---")
        try:
            # textareaに入力を試行
            await note_poster.page.fill('textarea', amazon_url, timeout=5000)
            logger.info(f"✅ URL入力成功: {amazon_url}")
        except Exception as e:
            logger.error(f"❌ URL入力失敗: {e}")
            # 代替方法を試行
            try:
                await note_poster.page.fill('input[type="url"]', amazon_url, timeout=3000)
                logger.info(f"✅ URL入力成功（代替方法）: {amazon_url}")
            except Exception as e2:
                logger.error(f"❌ URL入力失敗（代替方法も失敗）: {e2}")
                return
        
        # ステップ6: 適用ボタンの確認とクリック
        logger.info("--- ステップ6: 適用ボタン確認 ---")
        apply_button_check = await note_poster.page.evaluate("""
        () => {
            const buttons = Array.from(document.querySelectorAll('button'));
            const applyButtons = buttons.filter(btn => 
                btn.textContent.includes('適用') || 
                btn.textContent.includes('Apply') ||
                btn.type === 'submit'
            );
            
            return {
                totalButtons: buttons.length,
                applyButtonCount: applyButtons.length,
                applyButtons: applyButtons.map(btn => ({
                    text: btn.textContent,
                    type: btn.type,
                    visible: btn.offsetParent !== null,
                    disabled: btn.disabled
                }))
            };
        }
        """)
        
        logger.info(f"適用ボタン確認: {apply_button_check}")
        
        # 適用ボタンをクリック
        apply_success = False
        apply_selectors = [
            'button:has-text("適用")',
            'button[type="submit"]',
            'button:contains("適用")'
        ]
        
        for selector in apply_selectors:
            try:
                await note_poster.page.click(selector, timeout=3000)
                logger.info(f"✅ 適用ボタンクリック成功: {selector}")
                apply_success = True
                break
            except Exception as e:
                logger.warning(f"適用ボタンクリック失敗 ({selector}): {e}")
                continue
        
        if not apply_success:
            # JavaScriptで直接クリック
            try:
                js_result = await note_poster.page.evaluate("""
                () => {
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const applyButton = buttons.find(btn => 
                        btn.textContent.includes('適用') || 
                        btn.textContent.includes('Apply') ||
                        btn.type === 'submit'
                    );
                    if (applyButton) {
                        applyButton.click();
                        return { success: true, buttonText: applyButton.textContent };
                    }
                    return { success: false, error: '適用ボタンが見つかりません' };
                }
                """)
                
                if js_result['success']:
                    logger.info(f"✅ JavaScriptで適用ボタンクリック成功: {js_result['buttonText']}")
                    apply_success = True
                else:
                    logger.error(f"❌ JavaScriptでも適用ボタンクリック失敗: {js_result['error']}")
            except Exception as e:
                logger.error(f"❌ JavaScript適用ボタンクリック失敗: {e}")
        
        if apply_success:
            # リンク適用後の確認
            await asyncio.sleep(3)
            
            # ステップ7: リンク作成結果の確認
            logger.info("--- ステップ7: リンク作成結果確認 ---")
            link_check = await note_poster.page.evaluate("""
            () => {
                const contentDiv = document.querySelector('div[contenteditable="true"]');
                if (!contentDiv) return { success: false, error: '本文エリアが見つかりません' };
                
                const links = contentDiv.querySelectorAll('a');
                const linkData = Array.from(links).map(link => ({
                    text: link.textContent,
                    href: link.href,
                    visible: link.offsetParent !== null
                }));
                
                return {
                    success: true,
                    linkCount: links.length,
                    links: linkData,
                    contentText: contentDiv.textContent
                };
            }
            """)
            
            logger.info(f"リンク作成結果: {link_check}")
            
            if link_check['success'] and link_check['linkCount'] > 0:
                logger.info("🎉 リンク作成成功！")
                for i, link in enumerate(link_check['links']):
                    logger.info(f"  リンク{i+1}: {link['text']} → {link['href']}")
            else:
                logger.error("❌ リンクが作成されていません")
        else:
            logger.error("❌ 適用ボタンクリックに失敗したため、リンクは作成されませんでした")
        
        # 結果の最終確認
        logger.info("=== 最終結果確認 ===")
        if apply_success:
            logger.info("🎉 リンク作成処理が完了しました")
        else:
            logger.error("❌ リンク作成処理に失敗しました")
        
    except Exception as e:
        logger.error(f"デバッグ中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # ブラウザを閉じる
        if 'note_poster' in locals():
            await note_poster.close_browser()
        
        logger.info("=== 詳細リンク作成デバッグ完了 ===")

if __name__ == "__main__":
    asyncio.run(debug_link_creation())

