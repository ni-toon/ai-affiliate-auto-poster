"""
メインコントローラー
全機能を統合し、記事生成からSNS投稿までの一連の流れを制御する
"""

import asyncio
import json
import os
import sys
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import schedule
import time

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.product_research import ProductResearcher
from modules.article_generator import ArticleGenerator
from modules.note_poster import NotePoster

class MainController:
    def __init__(self, config_file: str = "config/config.json"):
        self.config = self.load_config(config_file)
        self.setup_logging()
        
        # 各モジュールの初期化
        self.product_researcher = ProductResearcher(
            amazon_associate_id=self.config['amazon']['associate_id']
        )
        
        self.article_generator = ArticleGenerator(
            openai_api_key=self.config['openai']['api_key']
        )
        
        self.note_poster = NotePoster(
            username=self.config['note']['username'],
            password=self.config['note']['password'],
            headless=self.config.get('browser', {}).get('headless', True)
        )
        
        # 統計情報
        self.daily_stats = {
            'articles_generated': 0,
            'note_posts_success': 0,
            'errors': []
        }
    
    def load_config(self, config_file: str) -> Dict:
        """設定ファイルを読み込み"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 設定ファイルの検証
            self.validate_config(config)
            return config
            
        except FileNotFoundError:
            print(f"設定ファイル {config_file} が見つかりません")
            
            # テンプレートファイルが存在するかチェック
            template_file = config_file + ".template"
            if os.path.exists(template_file):
                print(f"テンプレートファイル {template_file} から設定ファイルを作成します")
                # テンプレートをコピー
                import shutil
                shutil.copy(template_file, config_file)
                print(f"設定ファイル {config_file} を作成しました。必要な情報を入力してから再実行してください。")
                sys.exit(1)
            else:
                return self.create_default_config(config_file)
        except json.JSONDecodeError as e:
            print(f"設定ファイルのJSON形式が正しくありません: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"設定ファイル読み込みエラー: {e}")
            sys.exit(1)
    
    def validate_config(self, config: Dict):
        """設定ファイルの内容を検証"""
        required_keys = {
            'openai': ['api_key'],
            'amazon': ['associate_id'],
            'note': ['username', 'password'],
            'x': ['username', 'password'],
            'schedule': ['daily_posts', 'start_time', 'end_time'],
            'browser': ['headless']
        }
        
        for section, keys in required_keys.items():
            if section not in config:
                raise ValueError(f"設定ファイルに '{section}' セクションがありません")
            
            for key in keys:
                if key not in config[section]:
                    raise ValueError(f"設定ファイルの '{section}' セクションに '{key}' がありません")
                
                # プレースホルダー値のチェック
                value = config[section][key]
                if isinstance(value, str) and ('your-' in value or 'here' in value):
                    raise ValueError(f"'{section}.{key}' にプレースホルダー値が設定されています。実際の値を入力してください。")
    
    def create_default_config(self, config_file: str) -> Dict:
        """デフォルト設定を作成"""
        default_config = {
            "openai": {
                "api_key": "your-openai-api-key-here"
            },
            "amazon": {
                "associate_id": "your-amazon-associate-id-here"
            },
            "note": {
                "username": "your-note-username",
                "password": "your-note-password"
            },
            "x": {
                "username": "your-x-username",
                "password": "your-x-password"
            },
            "schedule": {
                "daily_posts": 5,
                "start_time": "09:00",
                "end_time": "21:00",
                "min_interval_minutes": 60,
                "max_interval_minutes": 180
            },
            "browser": {
                "headless": True
            }
        }
        
        # 設定ファイルを作成
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        
        return default_config
    
    def setup_logging(self):
        """ログ設定"""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"main_{datetime.now().strftime('%Y%m%d')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    async def generate_and_post_article(self) -> bool:
        """記事生成からSNS投稿までの一連の流れを実行"""
        try:
            self.logger.info("記事生成・投稿プロセス開始")
            
            # 1. 記事タイプをランダム選択
            article_type = random.choice(["レビュー", "ハウツー", "商品紹介"])
            self.logger.info(f"記事タイプ: {article_type}")
            
            # 2. 商品情報を取得
            products = self.product_researcher.get_products_for_article(article_type, 3)
            if not products:
                self.logger.error("商品情報の取得に失敗")
                return False
            
            self.logger.info(f"選択された商品: {[p['name'] for p in products]}")
            
            # 3. 記事を生成
            article_data = self.article_generator.generate_complete_article(products, article_type)
            self.daily_stats['articles_generated'] += 1
            
            self.logger.info(f"記事生成完了: {article_data['title']}")
            
            # 4. noteに投稿
            await self.note_poster.start_browser()
            
            # ログイン
            if not await self.note_poster.login():
                self.logger.error("noteログインに失敗")
                await self.note_poster.close_browser()
                return False
            
            # 記事投稿
            success = await self.note_poster.post_article(
                article_data['title'],
                article_data['content'],
                article_data['tags']
            )
            
            await self.note_poster.close_browser()
            
            if not success:
                self.logger.error("note投稿に失敗")
                self.daily_stats['errors'].append("note投稿失敗")
                return False
            
            # 投稿成功時のURL（実際のURLは取得できないため、成功フラグで判定）
            note_url = "投稿成功"
            
            self.daily_stats['note_posts_success'] += 1
            self.logger.info(f"note投稿成功: {note_url}")
            
            # 5. 記事データを保存
            self.save_article_data(article_data, note_url)
            
            self.logger.info("記事生成・投稿プロセス完了")
            return True
            
        except Exception as e:
            self.logger.error(f"記事生成・投稿プロセスでエラー: {e}")
            self.daily_stats['errors'].append(str(e))
            return False
    
    def save_article_data(self, article_data: Dict, note_url: str):
        """記事データを保存"""
        try:
            data_dir = "data"
            os.makedirs(data_dir, exist_ok=True)
            
            # 記事データファイル
            articles_file = os.path.join(data_dir, "generated_articles.json")
            
            article_record = {
                "title": article_data['title'],
                "content": article_data['content'],
                "tags": article_data['tags'],
                "article_type": article_data['article_type'],
                "category": article_data['category'],
                "note_url": note_url,
                "generated_at": article_data['generated_at'],
                "products": article_data['products']
            }
            
            if os.path.exists(articles_file):
                with open(articles_file, 'r', encoding='utf-8') as f:
                    articles = json.load(f)
            else:
                articles = []
            
            articles.append(article_record)
            
            with open(articles_file, 'w', encoding='utf-8') as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"記事データを保存: {articles_file}")
            
        except Exception as e:
            self.logger.error(f"記事データ保存エラー: {e}")
    
    def save_daily_stats(self):
        """日次統計を保存"""
        try:
            stats_dir = "data/stats"
            os.makedirs(stats_dir, exist_ok=True)
            
            today = datetime.now().strftime('%Y%m%d')
            stats_file = os.path.join(stats_dir, f"daily_stats_{today}.json")
            
            stats_data = {
                "date": today,
                "articles_generated": self.daily_stats['articles_generated'],
                "note_posts_success": self.daily_stats['note_posts_success'],
                "x_posts_success": self.daily_stats['x_posts_success'],
                "errors": self.daily_stats['errors'],
                "success_rate": {
                    "note": self.daily_stats['note_posts_success'] / max(1, self.daily_stats['articles_generated']),
                    "x": self.daily_stats['x_posts_success'] / max(1, self.daily_stats['articles_generated'])
                }
            }
            
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"日次統計を保存: {stats_file}")
            
        except Exception as e:
            self.logger.error(f"日次統計保存エラー: {e}")
    
    def reset_daily_stats(self):
        """日次統計をリセット"""
        self.daily_stats = {
            'articles_generated': 0,
            'note_posts_success': 0,
            'x_posts_success': 0,
            'errors': []
        }
    
    async def run_daily_schedule(self):
        """1日のスケジュールを実行"""
        daily_posts = self.config['schedule']['daily_posts']
        start_time = self.config['schedule']['start_time']
        end_time = self.config['schedule']['end_time']
        min_interval = self.config['schedule']['min_interval_minutes']
        max_interval = self.config['schedule']['max_interval_minutes']
        
        self.logger.info(f"本日の投稿スケジュール開始: {daily_posts}記事予定")
        
        for i in range(daily_posts):
            try:
                self.logger.info(f"記事 {i+1}/{daily_posts} の投稿開始")
                
                success = await self.generate_and_post_article()
                
                if success:
                    self.logger.info(f"記事 {i+1}/{daily_posts} の投稿完了")
                else:
                    self.logger.error(f"記事 {i+1}/{daily_posts} の投稿失敗")
                
                # 最後の記事でなければ待機
                if i < daily_posts - 1:
                    interval = random.randint(min_interval * 60, max_interval * 60)
                    self.logger.info(f"次の記事まで {interval//60}分待機")
                    await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"記事 {i+1} の処理でエラー: {e}")
                self.daily_stats['errors'].append(f"記事{i+1}: {str(e)}")
        
        # 日次統計を保存
        self.save_daily_stats()
        self.logger.info("本日の投稿スケジュール完了")
    
    def run_scheduler(self):
        """スケジューラーを実行"""
        self.logger.info("スケジューラー開始")
        
        # 毎日指定時間に実行
        schedule.every().day.at(self.config['schedule']['start_time']).do(
            lambda: asyncio.run(self.run_daily_schedule())
        )
        
        # 毎日0時に統計をリセット
        schedule.every().day.at("00:00").do(self.reset_daily_stats)
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1分ごとにチェック

# 使用例
async def main():
    """メイン実行関数"""
    controller = MainController()
    
    # テスト実行（1記事のみ）
    print("テスト実行: 1記事を生成・投稿します")
    success = await controller.generate_and_post_article()
    
    if success:
        print("テスト実行成功")
    else:
        print("テスト実行失敗")

if __name__ == "__main__":
    # テスト実行
    asyncio.run(main())

