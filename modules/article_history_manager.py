#!/usr/bin/env python3
"""
記事履歴管理モジュール
過去の記事データを保存・管理し、重複チェック機能を提供する
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)

class ArticleHistoryManager:
    def __init__(self, history_file: str = "data/article_history.json"):
        self.history_file = history_file
        self.history_data = self.load_history()
        
        # データディレクトリを作成
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
    
    def load_history(self) -> Dict:
        """記事履歴データを読み込み"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {
                    "articles": [],
                    "last_updated": None,
                    "total_articles": 0
                }
        except Exception as e:
            logger.error(f"履歴データの読み込みに失敗: {e}")
            return {
                "articles": [],
                "last_updated": None,
                "total_articles": 0
            }
    
    def save_history(self):
        """記事履歴データを保存"""
        try:
            self.history_data["last_updated"] = datetime.now().isoformat()
            self.history_data["total_articles"] = len(self.history_data["articles"])
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"記事履歴を保存しました: {self.history_file}")
        except Exception as e:
            logger.error(f"履歴データの保存に失敗: {e}")
    
    def add_article(self, article_data: Dict):
        """新しい記事を履歴に追加"""
        try:
            # 記事のハッシュ値を生成
            content_hash = self.generate_content_hash(article_data.get('content', ''))
            
            article_record = {
                "id": len(self.history_data["articles"]) + 1,
                "title": article_data.get('title', ''),
                "content": article_data.get('content', ''),
                "content_hash": content_hash,
                "content_length": len(article_data.get('content', '')),
                "category": article_data.get('category', ''),
                "article_type": article_data.get('article_type', ''),
                "tags": article_data.get('tags', []),
                "products": article_data.get('products', []),
                "created_at": datetime.now().isoformat(),
                "note_url": article_data.get('note_url', ''),
                "keywords": self.extract_keywords(article_data.get('content', ''))
            }
            
            self.history_data["articles"].append(article_record)
            self.save_history()
            
            logger.info(f"記事を履歴に追加: {article_record['title']}")
            return article_record["id"]
            
        except Exception as e:
            logger.error(f"記事の履歴追加に失敗: {e}")
            return None
    
    def generate_content_hash(self, content: str) -> str:
        """記事内容のハッシュ値を生成"""
        # 記事内容を正規化（空白、改行、記号を統一）
        normalized_content = re.sub(r'\s+', ' ', content.lower())
        normalized_content = re.sub(r'[^\w\s]', '', normalized_content)
        
        return hashlib.md5(normalized_content.encode('utf-8')).hexdigest()
    
    def extract_keywords(self, content: str) -> List[str]:
        """記事内容からキーワードを抽出"""
        # 簡易的なキーワード抽出（実際の実装では形態素解析を使用することを推奨）
        keywords = []
        
        # よく使われる単語を抽出
        common_words = [
            'おすすめ', '効果', 'メリット', 'デメリット', '使い方', '方法',
            '商品', 'レビュー', '評価', '価格', '機能', '特徴', '比較',
            '健康', 'ダイエット', 'フィットネス', '運動', 'トレーニング',
            '占い', 'タロット', '風水', '開運', 'スピリチュアル',
            '書籍', '本', '読書', '学習', '勉強', '知識'
        ]
        
        for word in common_words:
            if word in content:
                keywords.append(word)
        
        return list(set(keywords))  # 重複を除去
    
    def check_similarity(self, new_content: str, similarity_threshold: float = 0.7) -> Tuple[bool, List[Dict]]:
        """
        新しい記事内容と過去の記事の類似度をチェック
        
        Args:
            new_content: 新しい記事の内容
            similarity_threshold: 類似度の閾値（0.0-1.0）
        
        Returns:
            Tuple[bool, List[Dict]]: (類似記事が存在するか, 類似記事のリスト)
        """
        similar_articles = []
        
        try:
            for article in self.history_data["articles"]:
                similarity = self.calculate_similarity(new_content, article["content"])
                
                if similarity >= similarity_threshold:
                    similar_articles.append({
                        "id": article["id"],
                        "title": article["title"],
                        "similarity": similarity,
                        "created_at": article["created_at"],
                        "category": article.get("category", ""),
                        "article_type": article.get("article_type", "")
                    })
            
            # 類似度の高い順にソート
            similar_articles.sort(key=lambda x: x["similarity"], reverse=True)
            
            has_similar = len(similar_articles) > 0
            
            if has_similar:
                logger.warning(f"類似記事を{len(similar_articles)}件発見")
                for article in similar_articles[:3]:  # 上位3件をログ出力
                    logger.warning(f"  - {article['title']} (類似度: {article['similarity']:.2f})")
            
            return has_similar, similar_articles
            
        except Exception as e:
            logger.error(f"類似度チェックでエラー: {e}")
            return False, []
    
    def calculate_similarity(self, content1: str, content2: str) -> float:
        """
        2つの記事内容の類似度を計算
        
        Args:
            content1: 記事内容1
            content2: 記事内容2
        
        Returns:
            float: 類似度（0.0-1.0）
        """
        try:
            # 内容を正規化
            normalized1 = self.normalize_content(content1)
            normalized2 = self.normalize_content(content2)
            
            # SequenceMatcherを使用して類似度を計算
            similarity = SequenceMatcher(None, normalized1, normalized2).ratio()
            
            return similarity
            
        except Exception as e:
            logger.error(f"類似度計算でエラー: {e}")
            return 0.0
    
    def normalize_content(self, content: str) -> str:
        """記事内容を正規化"""
        # URLを除去
        content = re.sub(r'https?://[^\s]+', '', content)
        
        # 免責事項を除去
        content = re.sub(r'※本記事にはアフィリエイトリンクを含みます', '', content)
        
        # 改行と空白を正規化
        content = re.sub(r'\s+', ' ', content)
        
        # 記号を除去
        content = re.sub(r'[^\w\s]', '', content)
        
        return content.lower().strip()
    
    def get_recent_articles(self, limit: int = 10) -> List[Dict]:
        """最近の記事を取得"""
        try:
            articles = sorted(
                self.history_data["articles"],
                key=lambda x: x.get("created_at", ""),
                reverse=True
            )
            return articles[:limit]
        except Exception as e:
            logger.error(f"最近の記事取得でエラー: {e}")
            return []
    
    def get_articles_by_category(self, category: str) -> List[Dict]:
        """カテゴリ別の記事を取得"""
        try:
            return [
                article for article in self.history_data["articles"]
                if article.get("category", "").lower() == category.lower()
            ]
        except Exception as e:
            logger.error(f"カテゴリ別記事取得でエラー: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """記事統計情報を取得"""
        try:
            articles = self.history_data["articles"]
            
            # カテゴリ別統計
            category_stats = {}
            article_type_stats = {}
            
            for article in articles:
                category = article.get("category", "不明")
                article_type = article.get("article_type", "不明")
                
                category_stats[category] = category_stats.get(category, 0) + 1
                article_type_stats[article_type] = article_type_stats.get(article_type, 0) + 1
            
            return {
                "total_articles": len(articles),
                "category_distribution": category_stats,
                "article_type_distribution": article_type_stats,
                "last_updated": self.history_data.get("last_updated"),
                "average_content_length": sum(article.get("content_length", 0) for article in articles) / len(articles) if articles else 0
            }
            
        except Exception as e:
            logger.error(f"統計情報取得でエラー: {e}")
            return {}

# 使用例
if __name__ == "__main__":
    # テスト用のログ設定
    logging.basicConfig(level=logging.INFO)
    
    # 履歴マネージャーのインスタンス作成
    history_manager = ArticleHistoryManager()
    
    # テスト用記事データ
    test_article = {
        "title": "フィットネスバイクで健康的なダイエット",
        "content": "フィットネスバイクは自宅で手軽にできる有酸素運動です。継続することで健康的にダイエットができます。",
        "category": "フィットネス",
        "article_type": "レビュー",
        "tags": ["健康", "ダイエット", "フィットネス"]
    }
    
    # 記事を履歴に追加
    article_id = history_manager.add_article(test_article)
    print(f"記事ID: {article_id}")
    
    # 類似度チェック
    similar_content = "フィットネスバイクを使った健康的なダイエット方法について説明します。"
    has_similar, similar_articles = history_manager.check_similarity(similar_content)
    
    print(f"類似記事の存在: {has_similar}")
    if similar_articles:
        for article in similar_articles:
            print(f"  - {article['title']} (類似度: {article['similarity']:.2f})")
    
    # 統計情報を表示
    stats = history_manager.get_statistics()
    print(f"統計情報: {stats}")

