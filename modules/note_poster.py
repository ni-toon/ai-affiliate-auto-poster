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
                # 複数のセレクタを試行
                selectors = [
                    'input[placeholder="mail@example.com or note ID"]',
                    'input[type="email"]',
                    'input[name="email"]',
                    'input[placeholder*="mail"]',
                    'input[placeholder*="メール"]'
                ]
                
                input_filled = False
                for selector in selectors:
                    try:
                        await self.page.wait_for_selector(selector, timeout=5000)
                        await self.page.fill(selector, self.username)
                        logger.info(f"ユーザー名入力成功: {selector}")
                        input_filled = True
                        break
                    except:
                        continue
                
                if not input_filled:
                    logger.error("ユーザー名入力フィールドが見つかりません")
                    return False
                    
            except Exception as e:
                logger.error(f"ユーザー名入力に失敗: {e}")
                return False
            
            # パスワード入力
            try:
                # 複数のセレクタを試行
                selectors = [
                    'input[aria-label="パスワード"]',
                    'input[type="password"]',
                    'input[name="password"]',
                    'input[placeholder*="パスワード"]',
                    'input[placeholder*="password"]'
                ]
                
                input_filled = False
                for selector in selectors:
                    try:
                        await self.page.wait_for_selector(selector, timeout=5000)
                        await self.page.fill(selector, self.password)
                        logger.info(f"パスワード入力成功: {selector}")
                        input_filled = True
                        break
                    except:
                        continue
                
                if not input_filled:
                    logger.error("パスワード入力フィールドが見つかりません")
                    return False
                    
            except Exception as e:
                logger.error(f"パスワード入力に失敗: {e}")
                return False
            
            # ログインボタンクリック
            try:
                # 複数のセレクタを試行
                selectors = [
                    'button[type="submit"]',
                    'button:has-text("ログイン")',
                    'button:has-text("Login")',
                    'input[type="submit"]',
                    'form button'
                ]
                
                button_clicked = False
                for selector in selectors:
                    try:
                        await self.page.wait_for_selector(selector, timeout=5000)
                        await self.page.click(selector)
                        logger.info(f"ログインボタンクリック成功: {selector}")
                        button_clicked = True
                        break
                    except:
                        continue
                
                if not button_clicked:
                    logger.error("ログインボタンが見つかりません")
                    return False
                
                await self.page.wait_for_load_state('networkidle')
                
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
    
    async def post_article(self, title, content, tags):
        """記事を投稿する"""
        try:
            logger.info("記事投稿を開始")
            
            # 新規記事作成ページに移動
            await self.page.goto("https://note.com/new")
            await self.page.wait_for_load_state("networkidle")
            
            # タイトル入力
            logger.info("タイトルを入力中...")
            try:
                await self.page.wait_for_selector('textarea', timeout=10000)
                await self.page.fill('textarea', title)
                logger.info(f"タイトル入力成功: {title}")
            except Exception as e:
                logger.error(f"タイトル入力に失敗: {e}")
                return False
            
            # 本文入力（JavaScriptで直接入力）
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

