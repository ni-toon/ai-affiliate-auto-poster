"""
商品リサーチモジュール
占い、フィットネス、書籍分野の人気商品をリサーチし、
Amazonアソシエイトリンクを生成する機能を提供
"""

import random
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import time
from typing import List, Dict, Optional

class ProductResearcher:
    def __init__(self, amazon_associate_id: str = "ninomono3-22"):
        self.amazon_associate_id = amazon_associate_id
        self.categories = {
            "占い": [
                {
                    "name": "ゲッターズ飯田の五星三心占い2024完全版",
                    "category": "書籍",
                    "keywords": ["占い", "五星三心", "ゲッターズ飯田"],
                    "price_range": "1000-2000",
                    "description": "人気占い師ゲッターズ飯田による2024年の運勢占い本"
                },
                {
                    "name": "タロットカード 初心者向けセット",
                    "category": "占いグッズ",
                    "keywords": ["タロット", "初心者", "占い"],
                    "price_range": "2000-5000",
                    "description": "初心者でも使いやすいタロットカードセット"
                },
                {
                    "name": "78枚のカードで占う、いちばんていねいなタロット",
                    "category": "書籍",
                    "keywords": ["タロット", "占い", "入門書"],
                    "price_range": "1500-2500",
                    "description": "タロット占いの基本を学べる入門書"
                },
                {
                    "name": "パワーストーン ブレスレット",
                    "category": "アクセサリー",
                    "keywords": ["パワーストーン", "開運", "ブレスレット"],
                    "price_range": "3000-8000",
                    "description": "運気アップに効果があるとされるパワーストーンブレスレット"
                },
                {
                    "name": "風水開運グッズセット",
                    "category": "開運グッズ",
                    "keywords": ["風水", "開運", "インテリア"],
                    "price_range": "2000-6000",
                    "description": "風水に基づいた開運効果のあるインテリアグッズ"
                }
            ],
            "フィットネス": [
                {
                    "name": "STEADY フィットネスバイク エアロバイク",
                    "category": "フィットネス機器",
                    "keywords": ["エアロバイク", "家庭用", "静音"],
                    "price_range": "20000-40000",
                    "description": "家庭で使える静音設計のフィットネスバイク"
                },
                {
                    "name": "可変式ダンベル セット",
                    "category": "筋トレ器具",
                    "keywords": ["ダンベル", "可変式", "筋トレ"],
                    "price_range": "15000-30000",
                    "description": "重量調整可能な家庭用ダンベルセット"
                },
                {
                    "name": "腹筋ローラー",
                    "category": "筋トレ器具",
                    "keywords": ["腹筋", "ローラー", "コンパクト"],
                    "price_range": "1000-3000",
                    "description": "効果的な腹筋トレーニングができるローラー"
                },
                {
                    "name": "レジスタンスバンド セット",
                    "category": "筋トレ器具",
                    "keywords": ["レジスタンスバンド", "筋トレ", "チューブ"],
                    "price_range": "2000-5000",
                    "description": "様々な筋トレに使えるレジスタンスバンドセット"
                },
                {
                    "name": "ヨガマット",
                    "category": "フィットネス用品",
                    "keywords": ["ヨガ", "マット", "エクササイズ"],
                    "price_range": "3000-8000",
                    "description": "ヨガやストレッチに最適な高品質マット"
                },
                {
                    "name": "プロテイン ホエイ",
                    "category": "サプリメント",
                    "keywords": ["プロテイン", "ホエイ", "筋肉"],
                    "price_range": "3000-6000",
                    "description": "筋肉づくりに効果的なホエイプロテイン"
                }
            ],
            "書籍": [
                {
                    "name": "嫌われる勇気",
                    "category": "自己啓発",
                    "keywords": ["アドラー心理学", "自己啓発", "人間関係"],
                    "price_range": "1500-2000",
                    "description": "アドラー心理学を基にした人生を変える一冊"
                },
                {
                    "name": "変な家2 ～11の間取り図～",
                    "category": "エンターテイメント",
                    "keywords": ["ホラー", "間取り", "ミステリー"],
                    "price_range": "1200-1800",
                    "description": "話題のホラー小説第2弾"
                },
                {
                    "name": "ハーバード、スタンフォード、オックスフォード… 科学的に証明された すごい習慣大百科",
                    "category": "ビジネス・自己啓発",
                    "keywords": ["習慣", "科学", "自己改善"],
                    "price_range": "1600-2200",
                    "description": "科学的根拠に基づいた習慣改善の決定版"
                },
                {
                    "name": "世界の一流は「雑談」で何を話しているのか",
                    "category": "ビジネス",
                    "keywords": ["コミュニケーション", "雑談", "ビジネス"],
                    "price_range": "1400-1900",
                    "description": "一流の人々の雑談術を学べるビジネス書"
                },
                {
                    "name": "DIE WITH ZERO 人生が豊かになりすぎる究極のルール",
                    "category": "自己啓発・お金",
                    "keywords": ["お金", "人生設計", "資産運用"],
                    "price_range": "1600-2100",
                    "description": "お金と人生について考えさせられる話題の書"
                },
                {
                    "name": "改訂版 本当の自由を手に入れる お金の大学",
                    "category": "マネー・投資",
                    "keywords": ["お金", "投資", "節約"],
                    "price_range": "1500-2000",
                    "description": "お金の基本知識から投資まで学べる実用書"
                }
            ]
        }
    
    def get_random_product(self, category: str = None) -> Dict:
        """指定されたカテゴリまたはランダムなカテゴリから商品を選択"""
        if category and category in self.categories:
            selected_category = category
        else:
            selected_category = random.choice(list(self.categories.keys()))
        
        product = random.choice(self.categories[selected_category])
        product["selected_category"] = selected_category
        return product
    
    def generate_amazon_link(self, product_name: str, keywords: List[str] = None) -> str:
        """商品名とキーワードからAmazonアソシエイトリンクを生成"""
        if keywords:
            search_query = " ".join(keywords[:2])  # 最初の2つのキーワードを使用
        else:
            search_query = product_name
        
        encoded_query = quote(search_query)
        amazon_link = f"https://www.amazon.co.jp/s?k={encoded_query}&tag={self.amazon_associate_id}"
        return amazon_link
    
    def search_amazon_products(self, query: str, max_results: int = 5) -> List[Dict]:
        """Amazon検索結果から商品情報を取得（簡易版）"""
        # 実際の実装では、Amazon Product Advertising APIを使用することを推奨
        # ここでは、事前定義された商品データを返す
        results = []
        for category_name, products in self.categories.items():
            for product in products:
                if any(keyword.lower() in query.lower() for keyword in product["keywords"]):
                    product_info = product.copy()
                    product_info["amazon_link"] = self.generate_amazon_link(
                        product["name"], 
                        product["keywords"]
                    )
                    results.append(product_info)
                    if len(results) >= max_results:
                        break
            if len(results) >= max_results:
                break
        
        return results
    
    def get_products_for_article(self, article_type: str, count: int = 3) -> List[Dict]:
        """記事タイプに応じた商品を選択"""
        products = []
        
        if article_type == "レビュー":
            # レビュー記事では1つの商品に集中
            category = random.choice(list(self.categories.keys()))
            product = self.get_random_product(category)
            product["amazon_link"] = self.generate_amazon_link(
                product["name"], 
                product["keywords"]
            )
            products.append(product)
        
        elif article_type == "商品紹介":
            # 商品紹介では同じカテゴリから複数商品
            category = random.choice(list(self.categories.keys()))
            available_products = self.categories[category].copy()
            random.shuffle(available_products)
            
            for i in range(min(count, len(available_products))):
                product = available_products[i].copy()
                product["selected_category"] = category
                product["amazon_link"] = self.generate_amazon_link(
                    product["name"], 
                    product["keywords"]
                )
                products.append(product)
        
        elif article_type == "ハウツー":
            # ハウツー記事では関連商品を紹介
            category = random.choice(list(self.categories.keys()))
            product = self.get_random_product(category)
            product["amazon_link"] = self.generate_amazon_link(
                product["name"], 
                product["keywords"]
            )
            products.append(product)
        
        return products
    
    def save_product_data(self, filepath: str):
        """商品データをJSONファイルに保存"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.categories, f, ensure_ascii=False, indent=2)
    
    def load_product_data(self, filepath: str):
        """JSONファイルから商品データを読み込み"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.categories = json.load(f)
        except FileNotFoundError:
            print(f"商品データファイル {filepath} が見つかりません。デフォルトデータを使用します。")

# 使用例
if __name__ == "__main__":
    researcher = ProductResearcher()
    
    # ランダムな商品を取得
    product = researcher.get_random_product()
    print(f"選択された商品: {product['name']}")
    print(f"カテゴリ: {product['selected_category']}")
    print(f"Amazonリンク: {researcher.generate_amazon_link(product['name'], product['keywords'])}")
    
    # 記事用の商品を取得
    products = researcher.get_products_for_article("商品紹介", 3)
    print(f"\n商品紹介記事用の商品:")
    for i, p in enumerate(products, 1):
        print(f"{i}. {p['name']} - {p['amazon_link']}")

