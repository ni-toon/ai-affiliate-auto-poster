"""
AI記事生成モジュール
OpenAI APIを使用してアフィリエイト記事を自動生成する機能を提供
"""

import openai
import random
import json
from typing import Dict, List, Optional
from datetime import datetime
import re

class ArticleGenerator:
    def __init__(self, openai_api_key: str):
        # OpenAI APIキーの検証
        if not openai_api_key or openai_api_key == "your-openai-api-key-here":
            raise ValueError("有効なOpenAI APIキーが設定されていません。config.jsonを確認してください。")
        
        # OpenAIクライアントの初期化
        try:
            self.client = openai.OpenAI(api_key=openai_api_key)
        except Exception as e:
            raise ValueError(f"OpenAIクライアントの初期化に失敗しました: {e}")
            
        self.article_types = ["レビュー", "ハウツー", "商品紹介"]
        self.hashtags_pool = {
            "占い": ["#占い", "#タロット", "#スピリチュアル", "#開運", "#パワーストーン", "#風水"],
            "フィットネス": ["#フィットネス", "#筋トレ", "#ダイエット", "#健康", "#トレーニング", "#エクササイズ"],
            "書籍": ["#読書", "#本", "#ビジネス書", "#自己啓発", "#おすすめ本", "#書評"]
        }
    
    def generate_seo_title(self, product_info: Dict, article_type: str) -> str:
        """SEOを意識したタイトルを生成"""
        prompts = {
            "レビュー": f"「{product_info['name']}」の詳細レビュー記事のSEOタイトルを生成してください。商品の特徴やメリットを含め、検索されやすいタイトルにしてください。",
            "ハウツー": f"「{product_info['name']}」を使った{product_info['selected_category']}のハウツー記事のSEOタイトルを生成してください。初心者向けで実用的なタイトルにしてください。",
            "商品紹介": f"「{product_info['selected_category']}」分野のおすすめ商品紹介記事のSEOタイトルを生成してください。比較や選び方を含むタイトルにしてください。"
        }
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "あなたはSEOに精通したコピーライターです。検索エンジンで上位表示されやすく、クリックされやすいタイトルを生成してください。タイトルは30文字以内で、具体的で魅力的にしてください。"},
                    {"role": "user", "content": prompts[article_type]}
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            title = response.choices[0].message.content.strip()
            # タイトルから余分な記号や改行を除去
            title = re.sub(r'[「」『』]', '', title)
            title = title.replace('\n', '').strip()
            
            return title
        except Exception as e:
            print(f"タイトル生成エラー: {e}")
            # フォールバック用のタイトル
            fallback_titles = {
                "レビュー": f"{product_info['name']}の詳細レビュー！実際に使ってみた感想",
                "ハウツー": f"{product_info['selected_category']}初心者必見！{product_info['name']}の使い方ガイド",
                "商品紹介": f"{product_info['selected_category']}のおすすめ商品5選！選び方のポイントも解説"
            }
            return fallback_titles[article_type]
    
    def generate_article_content(self, products: List[Dict], article_type: str, title: str) -> str:
        """記事本文を生成"""
        main_product = products[0]
        category = main_product['selected_category']
        
        # 記事タイプ別のプロンプト
        prompts = {
            "レビュー": f"""
以下の商品について、詳細なレビュー記事を書いてください。

商品名: {main_product['name']}
カテゴリ: {category}
説明: {main_product['description']}
価格帯: {main_product['price_range']}円

記事の構成:
1. 概要（商品の基本情報と第一印象）
2. メリット（良い点を3つ程度）
3. デメリット（気になる点を2つ程度）
4. まとめ（総合評価と推奨する人）

要件:
- 500-1000文字程度
- 実際に使用したかのような具体的な表現
- 読者にとって有益な情報を含める
- 自然な文章で書く
- 商品名は記事中に2-3回登場させる
""",
            "ハウツー": f"""
以下の商品を使った{category}のハウツー記事を書いてください。

商品名: {main_product['name']}
カテゴリ: {category}
説明: {main_product['description']}

記事の構成:
1. 概要（なぜこの方法が効果的なのか）
2. メリット（この方法の利点）
3. デメリット（注意点や制限事項）
4. まとめ（実践のコツと期待できる効果）

要件:
- 500-1000文字程度
- 初心者でも理解できる内容
- 具体的な手順やコツを含める
- 実践的で役立つ情報
- 商品名は自然に組み込む
""",
            "商品紹介": f"""
{category}分野のおすすめ商品について紹介記事を書いてください。

主要商品: {main_product['name']}
その他の商品: {', '.join([p['name'] for p in products[1:]])}

記事の構成:
1. 概要（{category}商品選びの重要性）
2. メリット（おすすめ商品の共通する利点）
3. デメリット（選ぶ際の注意点）
4. まとめ（最終的な推奨とアドバイス）

要件:
- 500-1000文字程度
- 比較の観点を含める
- 読者の選択に役立つ情報
- 各商品の特徴を簡潔に説明
- 自然で読みやすい文章
"""
        }
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """あなたは日本語が母語の経験豊富なアフィリエイトライターです。以下の要件を厳守してください：

1. 自然で読みやすい日本語で書く
2. 文章の流れを重視し、段落間の繋がりを意識する
3. 読者目線で有益な情報を提供する
4. 商品の良い面だけでなく、客観的な視点も含める
5. 過度な宣伝文句は避け、信頼できる内容にする
6. 文字数は500-1000文字程度に収める
7. 見出しは「##」を使用してMarkdown形式で記述する"""},
                    {"role": "user", "content": prompts[article_type]}
                ],
                max_tokens=1500,
                temperature=0.6  # 温度を下げて一貫性を向上
            )
            
            content = response.choices[0].message.content.strip()
            return content
        except Exception as e:
            print(f"記事生成エラー: {e}")
            return self._generate_fallback_content(products, article_type)
    
    def _generate_fallback_content(self, products: List[Dict], article_type: str) -> str:
        """APIエラー時のフォールバック記事"""
        main_product = products[0]
        category = main_product['selected_category']
        
        fallback_content = f"""
## 概要

{category}分野で注目を集めている「{main_product['name']}」について詳しくご紹介します。{main_product['description']}として、多くの方に愛用されています。

## メリット

この商品の主な利点は以下の通りです：

1. **使いやすさ**: 初心者の方でも簡単に始められる設計になっています。
2. **コストパフォーマンス**: {main_product['price_range']}円という価格帯で、十分な価値を提供します。
3. **信頼性**: 多くのユーザーから高い評価を得ている実績があります。

## デメリット

一方で、以下の点にご注意ください：

1. **個人差**: 効果や使用感には個人差があります。
2. **継続の必要性**: 最大限の効果を得るには継続的な使用が重要です。

## まとめ

「{main_product['name']}」は、{category}に興味のある方にとって価値のある選択肢です。特に初心者の方や、コストパフォーマンスを重視する方におすすめできます。
"""
        return fallback_content
    
    def insert_affiliate_links(self, content: str, products: List[Dict]) -> str:
        """記事中にアフィリエイトリンクを自然に挿入"""
        # アフィリエイト免責事項を冒頭に追加
        disclaimer = "※本記事にはアフィリエイトリンクを含みます\n\n"
        
        # 商品名の後にリンクを挿入（noteに適した形式）
        modified_content = content
        for product in products:
            product_name = product['name']
            amazon_link = product['amazon_link']
            
            # 商品名の後にプレーンテキストリンクを追加（最初の出現のみ）
            pattern = f"({re.escape(product_name)})"
            replacement = f"\\1\n\n▼ Amazon詳細ページ\n{amazon_link}\n"
            modified_content = re.sub(pattern, replacement, modified_content, count=1)
        
        return disclaimer + modified_content
    
    def generate_note_tags(self, category: str, article_type: str) -> List[str]:
        """note用のタグを生成"""
        base_tags = self.hashtags_pool.get(category, [])
        article_tags = {
            "レビュー": ["#レビュー", "#体験談", "#口コミ"],
            "ハウツー": ["#ハウツー", "#初心者向け", "#使い方"],
            "商品紹介": ["#おすすめ", "#比較", "#選び方"]
        }
        
        # カテゴリタグ2-3個 + 記事タイプタグ2個を選択
        selected_tags = random.sample(base_tags, min(3, len(base_tags)))
        selected_tags.extend(random.sample(article_tags[article_type], 2))
        
        return selected_tags[:5]  # 最大5個
    
    def generate_x_post_patterns(self, title: str, note_url: str, category: str) -> List[str]:
        """X投稿用の複数パターンを生成"""
        hashtags = random.sample(self.hashtags_pool.get(category, []), 2)
        hashtag_str = " ".join(hashtags)
        
        patterns = [
            f"📝 新記事を公開しました！\n\n{title}\n\n{note_url}\n\n{hashtag_str}",
            f"✨ {title}\n\n詳しくはこちら👇\n{note_url}\n\n{hashtag_str}",
            f"🔍 {category}について書きました\n\n{title}\n\n{note_url}\n\n{hashtag_str}"
        ]
        
        return patterns
    
    def generate_complete_article(self, products: List[Dict], article_type: str = None) -> Dict:
        """完全な記事を生成（タイトル、本文、タグ、X投稿文）"""
        if not article_type:
            article_type = random.choice(self.article_types)
        
        main_product = products[0]
        category = main_product['selected_category']
        
        # タイトル生成
        title = self.generate_seo_title(main_product, article_type)
        
        # 記事本文生成
        content = self.generate_article_content(products, article_type, title)
        
        # アフィリエイトリンク挿入
        final_content = self.insert_affiliate_links(content, products)
        
        # タグ生成
        tags = self.generate_note_tags(category, article_type)
        
        # X投稿パターン生成
        x_patterns = self.generate_x_post_patterns(title, "NOTE_URL_PLACEHOLDER", category)
        
        return {
            "title": title,
            "content": final_content,
            "tags": tags,
            "x_post_patterns": x_patterns,
            "article_type": article_type,
            "category": category,
            "products": products,
            "generated_at": datetime.now().isoformat()
        }

# 使用例
if __name__ == "__main__":
    # テスト用のOpenAI APIキー（実際の使用時は環境変数から取得）
    api_key = "your-openai-api-key"
    generator = ArticleGenerator(api_key)
    
    # テスト用商品データ
    test_products = [{
        "name": "テスト商品",
        "selected_category": "書籍",
        "description": "テスト用の商品説明",
        "price_range": "1000-2000",
        "amazon_link": "https://amazon.co.jp/test"
    }]
    
    # 記事生成テスト
    article = generator.generate_complete_article(test_products, "レビュー")
    print(f"タイトル: {article['title']}")
    print(f"タグ: {', '.join(article['tags'])}")
    print(f"記事タイプ: {article['article_type']}")
    print(f"本文:\n{article['content'][:200]}...")

