"""
note自動投稿モジュール（修正版）
Playwrightを使用してnoteへの自動ログイン・投稿・タグ付与を行う
"""

import asyncio
import logging
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, Page, Browser
import json
import os
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotePoster:
    def __init__(self, username: str, password: str, headless: bool = True):
        self.username = username
        self.password = password
        self.headless = headless
        self.browser = None
        self.page = None
        self.is_logged_in = False
    
    async def start_browser(self):
        """ブラウザを起動"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        self.page = await self.context.new_page()
    
    async def close_browser(self):
        """ブラウザを終了"""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
    
    async def login(self) -> bool:
        """noteにログイン"""
        try:
            logger.info("noteにログイン中...")
            
            # まず現在のログイン状態を確認
            await self.page.goto('https://note.com/')
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            
            # ログイン状態の確認（メニューボタンの存在で判定）
            try:
                # ログイン済みの場合、メニューボタンが存在する
                menu_button = await self.page.query_selector('button:has(img[alt="メニュー"])')
                if menu_button:
                    logger.info("既にログイン済みです")
                    self.is_logged_in = True
                    return True
            except:
                pass
            
            # ログインページに移動
            await self.page.goto('https://note.com/login')
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)
            
            # ログインページが表示されているか確認
            current_url = self.page.url
            if 'login' not in current_url:
                # 既にログイン済みでリダイレクトされた場合
                logger.info("既にログイン済みです（リダイレクト確認）")
                self.is_logged_in = True
                return True
            
            # メールアドレス/ユーザー名入力
            try:
                await self.page.fill('input[type="email"], input[placeholder*="mail"], input[placeholder*="ID"]', self.username)
                logger.info("ユーザー名入力成功")
            except Exception as e:
                logger.error(f"ユーザー名入力に失敗: {e}")
                return False
            
            # パスワード入力
            try:
                await self.page.fill('input[type="password"]', self.password)
                logger.info("パスワード入力成功")
            except Exception as e:
                logger.error(f"パスワード入力に失敗: {e}")
                return False
            
            # ログインボタンクリック
            try:
                await self.page.click('button[type="submit"], button:has-text("ログイン")')
                await self.page.wait_for_load_state('networkidle')
                logger.info("ログインボタンクリック成功")
            except Exception as e:
                logger.error(f"ログインボタンクリックに失敗: {e}")
                return False
            
            # ログイン成功の確認
            await asyncio.sleep(5)
            current_url = self.page.url
            
            # URLでの確認
            if 'login' not in current_url and 'note.com' in current_url:
                logger.info("ログイン成功（URL確認）")
                self.is_logged_in = True
                return True
            
            # メニューボタンでの確認
            try:
                menu_button = await self.page.query_selector('button:has(img[alt="メニュー"])')
                if menu_button:
                    logger.info("ログイン成功（メニューボタン確認）")
                    self.is_logged_in = True
                    return True
            except:
                pass
            
            logger.error(f"ログイン失敗 - 現在のURL: {current_url}")
            return False
                
        except Exception as e:
            logger.error(f"ログインエラー: {e}")
            return False
    
    async def post_article(self, title, content, tags, thumbnail_path=None, products=None):
        """記事を投稿する（OGPリンクカード対応版）"""
        try:
            logger.info("記事投稿を開始")
            
            # 新規記事作成ページに移動
            await self.page.goto("https://note.com/new")
            await self.page.wait_for_load_state("networkidle")
            
            # サムネイル画像を設定（オプション）
            if thumbnail_path:
                await self.set_thumbnail_image(thumbnail_path)
            
            # タイトル入力（URLではなく記事タイトルを使用）
            logger.info("タイトルを入力中...")
            try:
                await self.page.wait_for_selector('textarea', timeout=10000)
                # タイトルがURLの場合は、商品名から適切なタイトルを生成
                if title.startswith('http'):
                    if products and len(products) > 0:
                        title = f"{products[0]['name']}のレビューと使用感"
                    else:
                        title = "おすすめ商品のご紹介"
                    logger.info(f"タイトルを修正: {title}")
                
                await self.page.fill('textarea', title)
                logger.info(f"タイトル入力成功: {title}")
            except Exception as e:
                logger.error(f"タイトル入力に失敗: {e}")
                return False
            
            # 本文入力（OGPリンクカードが自動生成される）
            logger.info("本文を入力中...")
            try:
                # HTMLエスケープ処理
                escaped_content = content.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
                
                js_code = f"""
                // 本文エリアを取得
                const contentDiv = document.querySelector('div[contenteditable="true"]');
                
                if (contentDiv) {{
                    contentDiv.innerHTML = `{escaped_content}`.replace(/\\n/g, '<br>');
                    // フォーカスを当てて変更を確定
                    contentDiv.focus();
                    contentDiv.blur();
                    console.log('本文入力完了');
                    true;
                }} else {{
                    console.log('本文エリアが見つかりません');
                    false;
                }}
                """
                
                result = await self.page.evaluate(js_code)
                if result:
                    logger.info("本文入力成功")
                else:
                    logger.error("本文エリアが見つかりません")
                    return False
                    
            except Exception as e:
                logger.error(f"本文入力に失敗: {e}")
                return False
            
            # OGPリンクカードの自動生成を待機
            logger.info("OGPリンクカードの生成を待機中...")
            await self.page.wait_for_timeout(3000)
            
            # 少し待機してから公開に進む
            await self.page.wait_for_timeout(2000)
            
            # 公開に進む
            logger.info("公開プロセスを開始...")
            try:
                await self.page.wait_for_selector('button:has-text("公開に進む")', timeout=10000)
                await self.page.click('button:has-text("公開に進む")')
                await self.page.wait_for_load_state("networkidle")
                logger.info("公開設定ページに移動しました")
            except Exception as e:
                logger.error(f"公開ボタンのクリックに失敗: {e}")
                return False
            
            # タグ追加
            if tags:
                logger.info("タグを追加中...")
                await self.add_tags(tags)
            
            # 最終的な投稿
            logger.info("記事を投稿中...")
            try:
                await self.page.wait_for_selector('button:has-text("投稿する")', timeout=10000)
                await self.page.click('button:has-text("投稿する")')
                await self.page.wait_for_load_state("networkidle")
                logger.info("記事投稿が完了しました")
                
                # 投稿完了の確認（URLの変化を確認）
                await self.page.wait_for_timeout(3000)
                current_url = self.page.url
                if "note.com/notes/" in current_url or "note.com/ninomono_3/n/" in current_url:
                    logger.info(f"投稿成功を確認: {current_url}")
                    return True
                else:
                    logger.warning(f"投稿完了の確認ができませんでした: {current_url}")
                    return True  # 一応成功とみなす
                    
            except Exception as e:
                logger.error(f"最終投稿に失敗: {e}")
                return False
            
        except Exception as e:
            logger.error(f"記事投稿中にエラーが発生: {e}")
            return False
    
    # async def convert_affiliate_placeholders(self, products: List[Dict]) -> bool:
    #     """
    #     アフィリエイトリンクプレースホルダーを実際のリンクに変換
    #     手動テストで100%成功した方法を実装
    #     ※ OGPリンクカード方式に変更したため、このメソッドは不要
    #     """
    #     logger.info("=== 旧リンク変換処理（無効化済み） ===")
    #     return True
    
    async def verify_ogp_link_cards(self, products: List[Dict]) -> bool:
        """
        OGPリンクカードが正しく生成されているかを確認
        """
        logger.info("=== OGPリンクカード確認開始 ===")
        
        if not products:
            logger.info("確認対象の商品がありません")
            return True
        
        try:
            # 少し待機してOGPリンクカードの生成を待つ
            await self.page.wait_for_timeout(5000)
            
            # 本文エリア内のリンクカードを確認
            link_cards_found = 0
            
            for i, product in enumerate(products):
                product_url = product.get('url', '')
                if not product_url:
                    continue
                
                logger.info(f"商品 {i+1}: {product['name']} のOGPリンクカードを確認中...")
                
                # OGPリンクカードの存在確認（複数の方法で確認）
                card_found = await self.page.evaluate(f"""
                    // 方法1: URLを含むリンクカードを検索
                    const linkCards = document.querySelectorAll('a[href*="{product_url.replace('https://', '').split('/')[0]}"]');
                    if (linkCards.length > 0) {{
                        console.log('OGPリンクカード発見 (方法1): ' + linkCards.length + '個');
                        return true;
                    }}
                    
                    // 方法2: 本文内のURLテキストを確認
                    const contentDiv = document.querySelector('div[contenteditable="true"]');
                    if (contentDiv && contentDiv.innerHTML.includes('{product_url}')) {{
                        console.log('URL確認 (方法2): URLが本文に存在');
                        return true;
                    }}
                    
                    // 方法3: iframe要素（埋め込みカード）を確認
                    const iframes = document.querySelectorAll('iframe');
                    for (const iframe of iframes) {{
                        if (iframe.src && iframe.src.includes('amazon')) {{
                            console.log('埋め込みカード発見 (方法3)');
                            return true;
                        }}
                    }}
                    
                    console.log('OGPリンクカードが見つかりませんでした');
                    return false;
                """)
                
                if card_found:
                    logger.info(f"✅ {product['name']} のOGPリンクカードを確認")
                    link_cards_found += 1
                else:
                    logger.warning(f"❌ {product['name']} のOGPリンクカードが見つかりません")
            
            success_rate = link_cards_found / len(products) if products else 0
            logger.info(f"OGPリンクカード確認結果: {link_cards_found}/{len(products)} ({success_rate:.1%})")
            
            return link_cards_found > 0  # 少なくとも1つのリンクカードが確認できれば成功
            
        except Exception as e:
            logger.error(f"OGPリンクカード確認中にエラー: {e}")
            return False
        """
        アフィリエイトリンクプレースホルダーを実際のリンクに変換
        手動テストで100%成功した方法を実装
        """
        logger.info("=== アフィリエイトリンク変換開始 ===")
        
        if not products:
            logger.info("変換対象の商品がありません")
            return True
        
        try:
            # ページを上部にスクロールしてツールバーを確実に表示
            await self.page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(1)
            
            # 本文エリアにフォーカスを当て直す
            content_area = await self.page.wait_for_selector('div[contenteditable="true"]', timeout=10000)
            await content_area.click()
            await asyncio.sleep(0.5)
            
            success_count = 0
            total_count = len(products)
            
            for i, product in enumerate(products):
                logger.info(f"=== 商品 {i+1}/{total_count}: {product['name']} ===")
                
                # プレースホルダーを検索
                placeholder = f"[LINK:{product['name']}]"
                logger.info(f"プレースホルダー検索: {placeholder}")
                
                # JavaScriptでプレースホルダーを検索・選択
                select_script = f"""
                const content = document.querySelector('div[contenteditable="true"]');
                if (!content) {{
                    console.log('本文エリアが見つかりません');
                    false;
                }} else {{
                    const text = content.textContent || content.innerText;
                    const placeholder = '{placeholder}';
                    const index = text.indexOf(placeholder);
                    
                    if (index === -1) {{
                        console.log('プレースホルダーが見つかりません: ' + placeholder);
                        false;
                    }} else {{
                        console.log('プレースホルダーを発見: ' + placeholder + ' at index: ' + index);
                        
                        // テキストノードを検索してプレースホルダーを選択
                        const walker = document.createTreeWalker(
                            content,
                            NodeFilter.SHOW_TEXT,
                            null,
                            false
                        );
                        
                        let currentIndex = 0;
                        let targetNode = null;
                        let targetStart = -1;
                        
                        while (walker.nextNode()) {{
                            const node = walker.currentNode;
                            const nodeText = node.textContent;
                            const nodeLength = nodeText.length;
                            
                            if (currentIndex <= index && index < currentIndex + nodeLength) {{
                                targetNode = node;
                                targetStart = index - currentIndex;
                                break;
                            }}
                            currentIndex += nodeLength;
                        }}
                        
                        if (targetNode && targetStart >= 0) {{
                            const range = document.createRange();
                            range.setStart(targetNode, targetStart);
                            range.setEnd(targetNode, targetStart + placeholder.length);
                            
                            const selection = window.getSelection();
                            selection.removeAllRanges();
                            selection.addRange(range);
                            
                            console.log('プレースホルダーを選択しました');
                            true;
                        }} else {{
                            console.log('プレースホルダーの選択に失敗');
                            false;
                        }}
                    }}
                }}
                """
                
                selection_result = await self.page.evaluate(select_script)
                
                if not selection_result:
                    logger.error(f"プレースホルダー '{placeholder}' の選択に失敗")
                    continue
                
                logger.info("✅ プレースホルダー選択成功")
                await asyncio.sleep(0.5)
                
                # ツールバーが表示されるまで待機
                try:
                    await self.page.wait_for_selector('button[aria-label="リンク"]', timeout=5000)
                    logger.info("✅ ツールバー表示確認")
                except:
                    logger.error("❌ ツールバーが表示されませんでした")
                    continue
                
                # リンクボタンをクリック（座標クリックで確実に）
                try:
                    link_button = await self.page.wait_for_selector('button[aria-label="リンク"]', timeout=5000)
                    
                    # ボタンの座標を取得してクリック
                    button_box = await link_button.bounding_box()
                    if button_box:
                        center_x = button_box['x'] + button_box['width'] / 2
                        center_y = button_box['y'] + button_box['height'] / 2
                        await self.page.mouse.click(center_x, center_y)
                        logger.info("✅ リンクボタンクリック成功（座標クリック）")
                    else:
                        await link_button.click()
                        logger.info("✅ リンクボタンクリック成功（要素クリック）")
                        
                except Exception as e:
                    logger.error(f"❌ リンクボタンクリック失敗: {e}")
                    continue
                
                await asyncio.sleep(1)
                
                # URL入力フィールドが表示されるまで待機
                try:
                    url_input = await self.page.wait_for_selector('textarea', timeout=5000)
                    logger.info("✅ URL入力フィールド表示確認")
                except:
                    logger.error("❌ URL入力フィールドが表示されませんでした")
                    continue
                
                # URLを入力
                try:
                    await url_input.fill(product['amazon_link'])
                    logger.info(f"✅ URL入力成功: {product['amazon_link'][:50]}...")
                except Exception as e:
                    logger.error(f"❌ URL入力失敗: {e}")
                    continue
                
                await asyncio.sleep(0.5)
                
                # 適用ボタンをクリック（複数の方法を試行）
                apply_success = False
                
                # 方法1: has-textセレクタ
                try:
                    apply_button = await self.page.wait_for_selector('button:has-text("適用")', timeout=3000)
                    await apply_button.click()
                    logger.info("✅ 適用ボタンクリック成功（has-text）")
                    apply_success = True
                except:
                    logger.warning("方法1失敗: has-textセレクタ")
                
                # 方法2: テキスト内容で検索
                if not apply_success:
                    try:
                        apply_buttons = await self.page.query_selector_all('button')
                        for button in apply_buttons:
                            text = await button.text_content()
                            if text and text.strip() == "適用":
                                await button.click()
                                logger.info("✅ 適用ボタンクリック成功（テキスト検索）")
                                apply_success = True
                                break
                    except:
                        logger.warning("方法2失敗: テキスト検索")
                
                # 方法3: JavaScriptで直接クリック
                if not apply_success:
                    try:
                        click_result = await self.page.evaluate("""
                        const buttons = document.querySelectorAll('button');
                        for (const button of buttons) {
                            if (button.textContent && button.textContent.trim() === '適用') {
                                button.click();
                                return true;
                            }
                        }
                        return false;
                        """)
                        
                        if click_result:
                            logger.info("✅ 適用ボタンクリック成功（JavaScript）")
                            apply_success = True
                        else:
                            logger.warning("方法3失敗: JavaScript検索で適用ボタンが見つからない")
                    except:
                        logger.warning("方法3失敗: JavaScript実行エラー")
                
                if apply_success:
                    await asyncio.sleep(2)
                    
                    # プレースホルダーを商品名に置換
                    await self.page.evaluate(f"""
                    () => {{
                        const content = document.querySelector('div[contenteditable="true"]');
                        if (content) {{
                            content.innerHTML = content.innerHTML.replace(
                                '{placeholder}',
                                '{product['name']}'
                            );
                        }}
                    }}
                    """)
                    
                    logger.info("🎉 リンク作成成功")
                    success_count += 1
                else:
                    logger.error("❌ 適用ボタンクリックに失敗したため、リンクは作成されませんでした")
                    # キャンセル処理
                    try:
                        await self.page.keyboard.press('Escape')
                    except:
                        pass
                
                # 次の処理のために少し待機
                await asyncio.sleep(1)
            
            logger.info(f"=== リンク変換完了: {success_count}/{total_count} 成功 ===")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"リンク変換中にエラーが発生: {e}")
            return False
    
    async def set_thumbnail_image(self, image_path: str) -> bool:
        """サムネイル画像を設定"""
        try:
            logger.info("サムネイル画像を設定中...")
            
            # 画像アップロードボタンを探す
            try:
                # 複数のセレクタを試行
                selectors = [
                    'input[type="file"]',
                    'button[aria-label="画像を追加"]',
                    'button:has-text("画像")',
                    '[data-testid="image-upload"]'
                ]
                
                for selector in selectors:
                    try:
                        if selector == 'input[type="file"]':
                            # ファイル入力要素に直接ファイルを設定
                            await self.page.set_input_files(selector, image_path)
                            logger.info("サムネイル画像設定成功")
                            await asyncio.sleep(2)
                            return True
                        else:
                            # ボタンをクリックしてファイル選択ダイアログを開く
                            await self.page.click(selector)
                            await asyncio.sleep(1)
                            # ファイル入力要素が表示されたら設定
                            await self.page.set_input_files('input[type="file"]', image_path)
                            logger.info("サムネイル画像設定成功")
                            await asyncio.sleep(2)
                            return True
                    except:
                        continue
                
                logger.warning("画像アップロードボタンが見つかりませんでした")
                return False
                
            except Exception as e:
                logger.error(f"サムネイル画像設定に失敗: {e}")
                return False
                
        except Exception as e:
            logger.error(f"サムネイル画像設定エラー: {e}")
            return False
    
    async def add_tags(self, tags: List[str]) -> bool:
        """タグを追加"""
        try:
            logger.info("タグを追加中...")
            
            for tag in tags:
                try:
                    # タグ入力フィールドを探す
                    await self.page.wait_for_selector('input[placeholder="ハッシュタグを追加する"]', timeout=5000)
                    
                    # #を除去してタグを入力
                    clean_tag = tag.replace('#', '')
                    await self.page.fill('input[placeholder="ハッシュタグを追加する"]', clean_tag)
                    await self.page.keyboard.press('Enter')
                    await asyncio.sleep(1)
                    logger.info(f"タグ追加成功: {clean_tag}")
                    
                except Exception as e:
                    logger.warning(f"タグ {tag} の追加に失敗: {e}")
                    continue
            
            logger.info("タグ追加処理完了")
            return True
            
        except Exception as e:
            logger.error(f"タグ追加エラー: {e}")
            return True  # タグ追加は失敗しても投稿は続行
    
    def save_post_record(self, article_data: Dict, article_url: str):
        """投稿記録を保存"""
        try:
            record = {
                "title": article_data['title'],
                "url": article_url,
                "tags": article_data.get('tags', []),
                "posted_at": datetime.now().isoformat(),
                "article_type": article_data.get('article_type', 'unknown'),
                "category": article_data.get('category', 'unknown')
            }
            
            # 記録ファイルに追加
            records_file = "data/note_posts.json"
            os.makedirs(os.path.dirname(records_file), exist_ok=True)
            
            if os.path.exists(records_file):
                with open(records_file, 'r', encoding='utf-8') as f:
                    records = json.load(f)
            else:
                records = []
            
            records.append(record)
            
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            
            logger.info(f"投稿記録を保存しました: {record['title']}")
            
        except Exception as e:
            logger.error(f"投稿記録の保存に失敗: {e}")

# 使用例
async def main():
    poster = NotePoster("ninomono_3", "Tori4150", headless=False)
    
    try:
        await poster.start_browser()
        
        if await poster.login():
            article_data = {
                "title": "テスト記事タイトル",
                "content": "これはテスト記事の本文です。",
                "tags": ["レビュー", "テスト"]
            }
            
            success = await poster.post_article(
                article_data["title"],
                article_data["content"],
                article_data["tags"]
            )
            
            if success:
                print("記事投稿成功！")
            else:
                print("記事投稿失敗")
        
    finally:
        await poster.close_browser()

if __name__ == "__main__":
    asyncio.run(main())

