"""
X（旧Twitter）自動投稿モジュール
Playwrightを使用してXへの自動ログイン・投稿を行う
"""

import asyncio
import time
import random
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, Page, Browser
import json
import os
from datetime import datetime
import re

class XPoster:
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
        """Xにログイン"""
        try:
            print("Xにログイン中...")
            await self.page.goto('https://x.com/login')
            await self.page.wait_for_load_state('networkidle')
            
            # ユーザー名入力
            username_selectors = [
                'input[name="text"]',
                'input[autocomplete="username"]',
                '[data-testid="ocfEnterTextTextInput"]'
            ]
            
            username_filled = False
            for selector in username_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    await self.page.fill(selector, self.username)
                    username_filled = True
                    break
                except:
                    continue
            
            if not username_filled:
                print("ユーザー名入力フィールドが見つかりません")
                return False
            
            # 次へボタンをクリック
            next_selectors = [
                '[data-testid="LoginForm_Login_Button"]',
                'button:has-text("次へ")',
                'button:has-text("Next")'
            ]
            
            for selector in next_selectors:
                try:
                    await self.page.click(selector)
                    break
                except:
                    continue
            
            await asyncio.sleep(3)
            
            # パスワード入力
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                '[data-testid="ocfEnterTextTextInput"]'
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    await self.page.fill(selector, self.password)
                    password_filled = True
                    break
                except:
                    continue
            
            if not password_filled:
                print("パスワード入力フィールドが見つかりません")
                return False
            
            # ログインボタンをクリック
            login_selectors = [
                '[data-testid="LoginForm_Login_Button"]',
                'button:has-text("ログイン")',
                'button:has-text("Log in")'
            ]
            
            for selector in login_selectors:
                try:
                    await self.page.click(selector)
                    break
                except:
                    continue
            
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(5)
            
            # ログイン成功の確認
            current_url = self.page.url
            if 'home' in current_url or 'x.com' in current_url and 'login' not in current_url:
                print("ログイン成功")
                self.is_logged_in = True
                return True
            else:
                print("ログイン失敗")
                return False
                
        except Exception as e:
            print(f"ログインエラー: {e}")
            return False
    
    async def create_post(self, content: str) -> bool:
        """投稿を作成"""
        try:
            print("投稿を作成中...")
            
            # ホームページに移動（投稿フォームがある場所）
            await self.page.goto('https://x.com/home')
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)
            
            # 投稿フォームを探す
            tweet_selectors = [
                '[data-testid="tweetTextarea_0"]',
                '[data-testid="tweetTextarea"]',
                'div[contenteditable="true"][data-testid="tweetTextarea_0"]',
                'div[role="textbox"]'
            ]
            
            tweet_box_found = False
            for selector in tweet_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=10000)
                    await self.page.click(selector)
                    await asyncio.sleep(1)
                    
                    # 既存のコンテンツをクリア
                    await self.page.keyboard.press('Control+a')
                    await self.page.keyboard.press('Delete')
                    
                    # 投稿内容を入力
                    await self.page.type(selector, content, delay=100)
                    tweet_box_found = True
                    break
                except Exception as e:
                    print(f"セレクタ {selector} でエラー: {e}")
                    continue
            
            if not tweet_box_found:
                print("投稿フォームが見つかりません")
                return False
            
            await asyncio.sleep(2)
            
            # 投稿ボタンをクリック
            post_selectors = [
                '[data-testid="tweetButtonInline"]',
                '[data-testid="tweetButton"]',
                'button:has-text("投稿")',
                'button:has-text("Post")'
            ]
            
            posted = False
            for selector in post_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    await self.page.click(selector)
                    posted = True
                    break
                except:
                    continue
            
            if not posted:
                print("投稿ボタンが見つかりません")
                return False
            
            # 投稿完了を待つ
            await asyncio.sleep(5)
            print("投稿完了")
            return True
            
        except Exception as e:
            print(f"投稿作成エラー: {e}")
            return False
    
    def shorten_url(self, url: str) -> str:
        """URLを短縮（簡易版）"""
        # 実際の実装では、bit.lyやtinyurlなどのサービスを使用
        # ここでは簡易的にドメイン部分のみを表示
        if 'note.com' in url:
            return url.replace('https://note.com/', 'note.com/')
        return url
    
    def select_post_pattern(self, patterns: List[str]) -> str:
        """投稿パターンからランダムに選択"""
        return random.choice(patterns)
    
    async def post_article_promotion(self, article_data: Dict, note_url: str) -> bool:
        """記事宣伝投稿を作成"""
        try:
            if not self.is_logged_in:
                login_success = await self.login()
                if not login_success:
                    return False
            
            # 投稿パターンを選択
            patterns = article_data.get('x_post_patterns', [])
            if not patterns:
                # デフォルトパターンを生成
                patterns = [f"📝 新記事を公開しました！\n\n{article_data['title']}\n\n{note_url}"]
            
            selected_pattern = self.select_post_pattern(patterns)
            
            # URLを実際のnote URLに置換
            post_content = selected_pattern.replace('NOTE_URL_PLACEHOLDER', note_url)
            
            # 文字数制限チェック（Xは280文字制限）
            if len(post_content) > 280:
                # 長すぎる場合は短縮
                title = article_data['title']
                if len(title) > 100:
                    title = title[:97] + "..."
                
                short_url = self.shorten_url(note_url)
                post_content = f"📝 {title}\n\n{short_url}\n\n#記事更新"
            
            # 投稿実行
            success = await self.create_post(post_content)
            
            if success:
                # 投稿記録を保存
                self.save_post_record(article_data, note_url, post_content)
            
            return success
            
        except Exception as e:
            print(f"記事宣伝投稿エラー: {e}")
            return False
    
    def save_post_record(self, article_data: Dict, note_url: str, post_content: str):
        """投稿記録を保存"""
        try:
            record = {
                "title": article_data['title'],
                "note_url": note_url,
                "post_content": post_content,
                "posted_at": datetime.now().isoformat(),
                "article_type": article_data.get('article_type', 'unknown'),
                "category": article_data.get('category', 'unknown')
            }
            
            # 記録ファイルに追加
            records_file = "data/x_posts.json"
            os.makedirs(os.path.dirname(records_file), exist_ok=True)
            
            if os.path.exists(records_file):
                with open(records_file, 'r', encoding='utf-8') as f:
                    records = json.load(f)
            else:
                records = []
            
            records.append(record)
            
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            
            print(f"X投稿記録を保存: {records_file}")
            
        except Exception as e:
            print(f"X投稿記録保存エラー: {e}")
    
    async def wait_random_delay(self, min_seconds: int = 60, max_seconds: int = 300):
        """ランダムな待機時間（人間らしい動作のため）"""
        delay = random.randint(min_seconds, max_seconds)
        print(f"{delay}秒待機中...")
        await asyncio.sleep(delay)

# 使用例とテスト関数
async def test_x_posting():
    """X投稿のテスト"""
    poster = XPoster("ninomono3", "haruku1126", headless=False)
    
    try:
        await poster.start_browser()
        
        # テスト用記事データ
        test_article = {
            "title": "AI自動投稿システムのテスト記事",
            "x_post_patterns": [
                "📝 新記事を公開しました！\n\nAI自動投稿システムのテスト記事\n\nNOTE_URL_PLACEHOLDER\n\n#AI #自動化 #テスト"
            ],
            "article_type": "テスト",
            "category": "システム"
        }
        
        test_note_url = "https://note.com/ninomono_3/n/test123"
        
        # 記事宣伝投稿
        success = await poster.post_article_promotion(test_article, test_note_url)
        
        if success:
            print("X投稿成功")
        else:
            print("X投稿失敗")
    
    finally:
        await poster.close_browser()

if __name__ == "__main__":
    # テスト実行
    asyncio.run(test_x_posting())

