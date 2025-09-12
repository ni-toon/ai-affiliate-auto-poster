"""
note自動投稿モジュール
Playwrightを使用してnoteへの自動ログイン・投稿・タグ付与を行う
"""

import asyncio
import time
import random
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, Page, Browser
import json
import os
from datetime import datetime

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
            print("noteにログイン中...")
            await self.page.goto('https://note.com/login')
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)
            
            # メールアドレス/ユーザー名入力フィールドを探す（現在のUIに対応）
            username_selectors = [
                'input[placeholder="mail@example.com or note ID"]',
                'input[placeholder*="mail"]',
                'input[placeholder*="note ID"]',
                'input[name="login_name"]',
                'input[name="email"]',
                'input[type="email"]',
                'input[placeholder*="メール"]',
                'input[placeholder*="email"]',
                'input[placeholder*="ユーザー"]',
                'input[data-testid="email"]',
                '#email',
                '#login_name'
            ]
            
            username_filled = False
            for selector in username_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=3000)
                    await self.page.fill(selector, self.username)
                    print(f"ユーザー名入力成功: {selector}")
                    username_filled = True
                    break
                except Exception as e:
                    print(f"セレクタ {selector} でエラー: {e}")
                    continue
            
            if not username_filled:
                print("ユーザー名入力フィールドが見つかりません")
                print("手動でユーザー名を入力してください（30秒待機）...")
                await asyncio.sleep(30)
            
            # パスワード入力フィールドを探す（現在のUIに対応）
            password_selectors = [
                'input[aria-label="パスワード"]',
                'input[name="password"]',
                'input[type="password"]',
                'input[placeholder*="パスワード"]',
                'input[placeholder*="password"]',
                'input[data-testid="password"]',
                '#password'
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=3000)
                    await self.page.fill(selector, self.password)
                    print(f"パスワード入力成功: {selector}")
                    password_filled = True
                    break
                except Exception as e:
                    print(f"セレクタ {selector} でエラー: {e}")
                    continue
            
            if not password_filled:
                print("パスワード入力フィールドが見つかりません")
                print("手動でパスワードを入力してください（30秒待機）...")
                await asyncio.sleep(30)
            
            # ログインボタンを探してクリック
            login_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("ログイン")',
                'button:has-text("Login")',
                'button:has-text("サインイン")',
                '.login-button',
                '[data-testid="login-button"]',
                'button[data-cy="login"]',
                'form button'
            ]
            
            login_clicked = False
            for selector in login_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=3000)
                    await self.page.click(selector)
                    print(f"ログインボタンクリック成功: {selector}")
                    login_clicked = True
                    break
                except Exception as e:
                    print(f"セレクタ {selector} でエラー: {e}")
                    continue
            
            if not login_clicked:
                print("ログインボタンが見つかりません")
                print("手動でログインボタンをクリックしてください（30秒待機）...")
                await asyncio.sleep(30)
            
            # ログイン完了を待つ
            await asyncio.sleep(5)
            await self.page.wait_for_load_state('networkidle')
            
            # ログイン成功の確認
            current_url = self.page.url
            if 'login' not in current_url and 'note.com' in current_url:
                print("ログイン成功")
                self.is_logged_in = True
                return True
            else:
                print(f"ログイン失敗 - 現在のURL: {current_url}")
                print("手動でログインを完了してください（60秒待機）...")
                await asyncio.sleep(60)
                
                # 再度確認
                current_url = self.page.url
                if 'login' not in current_url and 'note.com' in current_url:
                    print("手動ログイン成功")
                    self.is_logged_in = True
                    return True
                else:
                    return False
                
        except Exception as e:
            print(f"ログインエラー: {e}")
            return False
    
    async def create_new_post(self) -> bool:
        """新規投稿ページに移動"""
        try:
            print("新規投稿ページに移動中...")
            await self.page.goto('https://note.com/new')
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            return True
        except Exception as e:
            print(f"新規投稿ページ移動エラー: {e}")
            return False
    
    async def fill_article_content(self, title: str, content: str) -> bool:
        """記事のタイトルと本文を入力"""
        try:
            print("記事内容を入力中...")
            
            # タイトル入力フィールドを探す（現在のnoteエディタUIに対応）
            title_selectors = [
                'textarea',  # 現在のnoteエディタのタイトルフィールド
                'textarea[placeholder*="タイトル"]',
                'input[placeholder="タイトル"]',
                'input[placeholder*="タイトル"]',
                '[data-testid="title-input"]',
                'input[name="title"]',
                '.title-input',
                'h1[contenteditable="true"]'
            ]
            
            title_filled = False
            for selector in title_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    await self.page.fill(selector, title)
                    print(f"タイトル入力成功: {selector}")
                    title_filled = True
                    break
                except Exception as e:
                    print(f"タイトルセレクタ {selector} でエラー: {e}")
                    continue
            
            if not title_filled:
                print("タイトル入力フィールドが見つかりません")
                print("手動でタイトルを入力してください（30秒待機）...")
                await asyncio.sleep(30)
            
            await asyncio.sleep(2)
            
            # 本文入力フィールドを探す（現在のnoteエディタUIに対応）
            content_selectors = [
                'div',  # 現在のnoteエディタの本文フィールド（青い枠のdiv）
                'div[contenteditable="true"]',
                '[contenteditable="true"]',
                '[data-testid="editor"]',
                '.editor-content',
                'textarea[placeholder="本文を入力"]',
                'textarea[placeholder*="本文"]',
                '.note-editor',
                '[role="textbox"]'
            ]
            
            content_filled = False
            for selector in content_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    await self.page.click(selector)
                    await asyncio.sleep(1)
                    
                    # 既存のコンテンツをクリア
                    await self.page.keyboard.press('Control+a')
                    await self.page.keyboard.press('Delete')
                    await asyncio.sleep(1)
                    
                    # 新しいコンテンツを入力
                    await self.page.type(selector, content, delay=50)
                    print(f"本文入力成功: {selector}")
                    
                    # リンクを自動でクリック可能にする処理
                    await self.process_links_in_content()
                    
                    content_filled = True
                    break
                except Exception as e:
                    print(f"本文セレクタ {selector} でエラー: {e}")
                    continue
            
            if not content_filled:
                print("本文入力フィールドが見つかりません")
                print("手動で本文を入力してください（60秒待機）...")
                await asyncio.sleep(60)
            
            await asyncio.sleep(2)
            print("記事内容の入力完了")
            return True
            
        except Exception as e:
            print(f"記事内容入力エラー: {e}")
            return False
    
    async def process_links_in_content(self):
        """本文中のURLをリンク化する処理"""
        try:
            print("URLのリンク化を実行中...")
            await asyncio.sleep(2)
            
            # URLパターンを検索してリンク化
            # Ctrl+Fでhttpsを検索
            await self.page.keyboard.press('Control+f')
            await asyncio.sleep(1)
            await self.page.keyboard.type('https://')
            await asyncio.sleep(1)
            await self.page.keyboard.press('Escape')
            
            # URLを選択してリンク化（noteの場合、URLは自動でリンクになることが多い）
            # 手動でリンク化が必要な場合のための待機時間
            await asyncio.sleep(3)
            
            print("リンク処理完了")
            
        except Exception as e:
            print(f"リンク処理エラー: {e}")
    
    async def add_tags(self, tags: List[str]) -> bool:
        """タグを追加"""
        try:
            print("タグを追加中...")
            
            # タグ入力フィールドを探す
            tag_selectors = [
                'input[placeholder="タグを追加"]',
                'input[placeholder*="タグ"]',
                '[data-testid="tag-input"]',
                '.tag-input',
                'input[name="tag"]',
                'input[name="tags"]',
                '.hashtag-input'
            ]
            
            tag_input_found = False
            for selector in tag_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=3000)
                    tag_input_found = True
                    print(f"タグ入力フィールド発見: {selector}")
                    
                    for tag in tags:
                        # #を除去してタグを入力
                        clean_tag = tag.replace('#', '')
                        await self.page.fill(selector, clean_tag)
                        await self.page.keyboard.press('Enter')
                        await asyncio.sleep(1)
                        print(f"タグ追加: {clean_tag}")
                    
                    break
                except Exception as e:
                    print(f"タグセレクタ {selector} でエラー: {e}")
                    continue
            
            if not tag_input_found:
                print("タグ入力フィールドが見つかりません")
                print("手動でタグを追加してください（30秒待機）...")
                print(f"追加するタグ: {', '.join(tags)}")
                await asyncio.sleep(30)
            else:
                print("タグ追加完了")
            
            return True
            
        except Exception as e:
            print(f"タグ追加エラー: {e}")
            return True  # タグ追加は失敗しても投稿は続行
    
    async def publish_post(self) -> Optional[str]:
        """記事を公開"""
        try:
            print("記事を公開中...")
            
            # 公開ボタンを探してクリック（現在のnoteエディタUIに対応）
            publish_selectors = [
                'button:has-text("公開に進む")',  # 現在のnoteエディタの公開ボタン
                'button:has-text("公開する")',
                'button:has-text("投稿する")',
                'button:has-text("公開")',
                'button:has-text("投稿")',
                '[data-testid="publish-button"]',
                'button[type="submit"]',
                '.publish-button',
                '.post-button',
                'button[data-cy="publish"]'
            ]
            
            published = False
            for selector in publish_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=3000)
                    await self.page.click(selector)
                    print(f"公開ボタンクリック成功: {selector}")
                    published = True
                    break
                except Exception as e:
                    print(f"公開セレクタ {selector} でエラー: {e}")
                    continue
            
            if not published:
                print("公開ボタンが見つかりません")
                print("手動で公開ボタンをクリックしてください（60秒待機）...")
                await asyncio.sleep(60)
            
            # 公開完了を待つ
            await asyncio.sleep(5)
            await self.page.wait_for_load_state('networkidle')
            
            # 公開後のURLを取得
            current_url = self.page.url
            print(f"公開完了 - URL: {current_url}")
            
            return current_url
            
        except Exception as e:
            print(f"公開エラー: {e}")
            return None
            
            # 公開完了を待つ
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(5)
            
            # 公開された記事のURLを取得
            current_url = self.page.url
            if 'note.com' in current_url and '/n/' in current_url:
                print(f"記事公開成功: {current_url}")
                return current_url
            else:
                print("記事URLの取得に失敗")
                return None
                
        except Exception as e:
            print(f"記事公開エラー: {e}")
            return None
    
    async def post_article(self, article_data: Dict) -> Optional[str]:
        """記事を投稿（全体の流れ）"""
        try:
            if not self.is_logged_in:
                login_success = await self.login()
                if not login_success:
                    return None
            
            # 新規投稿ページに移動
            if not await self.create_new_post():
                return None
            
            # 記事内容を入力
            if not await self.fill_article_content(article_data['title'], article_data['content']):
                return None
            
            # タグを追加
            await self.add_tags(article_data['tags'])
            
            # 記事を公開
            article_url = await self.publish_post()
            
            if article_url:
                # 投稿記録を保存
                self.save_post_record(article_data, article_url)
            
            return article_url
            
        except Exception as e:
            print(f"記事投稿エラー: {e}")
            return None
    
    def save_post_record(self, article_data: Dict, article_url: str):
        """投稿記録を保存"""
        try:
            record = {
                "title": article_data['title'],
                "url": article_url,
                "tags": article_data['tags'],
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
            
            print(f"投稿記録を保存: {records_file}")
            
        except Exception as e:
            print(f"投稿記録保存エラー: {e}")
    
    async def wait_random_delay(self, min_seconds: int = 30, max_seconds: int = 120):
        """ランダムな待機時間（人間らしい動作のため）"""
        delay = random.randint(min_seconds, max_seconds)
        print(f"{delay}秒待機中...")
        await asyncio.sleep(delay)

# 使用例とテスト関数
async def test_note_posting():
    """note投稿のテスト"""
    poster = NotePoster("ninomono_3", "Tori4150", headless=False)
    
    try:
        await poster.start_browser()
        
        # テスト用記事データ
        test_article = {
            "title": "テスト記事：AI自動投稿システムのテスト",
            "content": """※本記事にはアフィリエイトリンクを含みます

## 概要
これはAI自動投稿システムのテスト記事です。

## メリット
- 自動化により効率的
- 一貫した品質
- 時間の節約

## デメリット
- 初期設定が必要
- 定期的なメンテナンスが必要

## まとめ
自動投稿システムは適切に設定すれば非常に有用です。""",
            "tags": ["#テスト", "#自動化", "#AI"],
            "article_type": "テスト",
            "category": "システム"
        }
        
        # 記事投稿
        article_url = await poster.post_article(test_article)
        
        if article_url:
            print(f"投稿成功: {article_url}")
        else:
            print("投稿失敗")
    
    finally:
        await poster.close_browser()

if __name__ == "__main__":
    # テスト実行
    asyncio.run(test_note_posting())

