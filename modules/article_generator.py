"""
AI記事生成モジュール
OpenAI APIを使用してアフィリエイト記事を自動生成する機能を提供
"""

import openai
import random
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional
from .article_history_manager import ArticleHistoryManager
from .similarity_analyzer import SimilarityAnalyzer

logger = logging.getLogger(__name__)

class ArticleGenerator:
    def __init__(self, openai_api_key: str, enable_duplicate_check: bool = True):
        """
        記事生成器を初期化
        
        Args:
            openai_api_key: OpenAI APIキー
            enable_duplicate_check: 重複チェック機能を有効にするか
        """
        # OpenAI APIキーの検証
        if not openai_api_key or openai_api_key == "your-openai-api-key-here":
            raise ValueError("有効なOpenAI APIキーが設定されていません。config.jsonを確認してください。")
        
        # OpenAIクライアントの初期化
        try:
            self.client = openai.OpenAI(api_key=openai_api_key)
        except Exception as e:
            logger.error(f"OpenAIクライアントの初期化に失敗: {e}")
            raise
        
        # 重複チェック機能を初期化
        self.enable_duplicate_check = enable_duplicate_check
        if self.enable_duplicate_check:
            try:
                self.history_manager = ArticleHistoryManager()
                self.similarity_analyzer = SimilarityAnalyzer()
                logger.info("重複チェック機能を有効化しました")
            except Exception as e:
                logger.warning(f"重複チェック機能の初期化に失敗: {e}")
                self.enable_duplicate_check = False
                self.history_manager = None
                self.similarity_analyzer = None
        else:
            self.history_manager = None
            self.similarity_analyzer = None
            logger.info("重複チェック機能は無効です")
        self.article_types = ["レビュー", "ハウツー", "商品紹介"]
        self.hashtags_pool = {
            "占い": ["#占い", "#タロット", "#スピリチュアル", "#開運", "#パワーストーン", "#風水"],
            "フィットネス": ["#フィットネス", "#筋トレ", "#ダイエット", "#健康", "#トレーニング", "#エクササイズ"],
            "書籍": ["#読書", "#本", "#ビジネス書", "#自己啓発", "#おすすめ本", "#書評"],
            "家電・ガジェット": ["#家電", "#ガジェット", "#便利グッズ", "#最新家電", "#レビュー"],
            "美容・パーソナルケア": ["#美容", "#スキンケア", "#コスメ", "#ヘアケア", "#自分磨き"],
            "アウトドア・スポーツ": ["#アウトドア", "#キャンプ", "#スポーツ", "#登山", "#ランニング"],
            "ヘルスケア・見守り": ["#ヘルスケア", "#健康管理", "#見守り", "#セルフケア", "#健康"],
            "キッチン・時短家事": ["#キッチン", "#時短家事", "#便利グッズ", "#料理", "#暮らしの工夫"]
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
                model="gpt-4.1-mini",
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
        
        # ジャンル別の記事生成プロンプト
        genre_specific_prompts = self._get_genre_specific_prompt(category, main_product)
        
        # 記事タイプ別のプロンプト
        prompts = {
            "レビュー": f"""
以下の商品について、実際に使用したかのような詳細なレビュー記事を日本語で書いてください。

商品名: {main_product['name']}
カテゴリ: {category}
説明: {main_product['description']}
価格帯: {main_product['price_range']}円

{genre_specific_prompts}

記事の構成:
## 概要
商品の基本情報と第一印象を自然な文章で説明

## メリット
実際に使ってみて感じた良い点を3つ程度、具体的なエピソードを交えて説明

## デメリット
気になった点や注意すべき点を2つ程度、客観的に説明

## まとめ
総合評価と、どのような人におすすめかを明確に記述

要件:
- 500-1000文字程度
- 自然で読みやすい日本語
- 実体験に基づいた具体的な表現
- 読者にとって有益で信頼できる情報
- 商品名は記事中に2-3回自然に登場
- 過度な宣伝文句は避ける
""",
            "ハウツー": f"""
以下の商品を活用した{category}のハウツー記事を日本語で書いてください。

商品名: {main_product['name']}
カテゴリ: {category}
説明: {main_product['description']}

記事の構成:
## 概要
なぜこの方法が効果的なのか、背景と目的を説明

## メリット
この方法を実践することで得られる具体的な利点

## デメリット
注意点や制限事項、失敗しやすいポイント

## まとめ
実践のコツと期待できる効果、継続のポイント

要件:
- 500-1000文字程度
- 初心者でも理解できる分かりやすい説明
- 具体的な手順やコツを含める
- 実践的で役立つ情報
- 自然で読みやすい日本語
- 商品名は文脈に合わせて自然に組み込む
""",
            "商品紹介": f"""
{category}分野のおすすめ商品について、比較検討に役立つ紹介記事を日本語で書いてください。

主要商品: {main_product['name']}
その他の商品: {', '.join([p['name'] for p in products[1:]])}

記事の構成:
## 概要
{category}商品選びの重要性と、良い商品の見分け方

## メリット
おすすめ商品に共通する優れた特徴と利点

## デメリット
選ぶ際の注意点や、避けるべきポイント

## まとめ
最終的な推奨と、読者への具体的なアドバイス

要件:
- 500-1000文字程度
- 比較の観点を含めた客観的な評価
- 読者の選択に役立つ実用的な情報
- 各商品の特徴を簡潔に説明
- 自然で読みやすい日本語
- 押し売り感のない信頼できる内容
"""
        }
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
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
        """記事中にアフィリエイトリンクをOGPリンクカード形式で自然に挿入"""
        # アフィリエイト免責事項を冒頭に追加
        disclaimer = "※本記事にはアフィリエイトリンクを含みます\n\n"
        
        if not products:
            return disclaimer + content
        
        main_product = products[0]
        product_name = main_product['name']
        product_url = main_product.get('url', main_product.get('amazon_link', ''))
        
        # 記事の構造を解析
        sections = content.split('\n\n')
        modified_sections = []
        
        link_inserted = False
        
        for i, section in enumerate(sections):
            modified_sections.append(section)
            
            # メリット部分の後に自然な形でアフィリエイトリンクをOGPカード形式で挿入
            if ('## メリット' in section or 'メリット' in section) and not link_inserted and product_url:
                # 商品紹介文を追加
                intro_text = f"{product_name}は、多くの読者から高い評価を得ている商品です。詳細は以下からご確認いただけます。"
                modified_sections.append(intro_text)
                # OGPリンクカード生成のため、URLを単独行で配置
                modified_sections.append(product_url)
                link_inserted = True
        
        # もしまだリンクが挿入されていない場合は、記事の最後に自然な形で追加
        if not link_inserted and product_url:
            intro_text = f"今回ご紹介した{product_name}について、詳細は以下からご確認いただけます。"
            modified_sections.append(intro_text)
            # OGPリンクカード生成のため、URLを単独行で配置
            modified_sections.append(product_url)
        
        # 追加の商品がある場合は、まとめ部分に挿入
        if len(products) > 1:
            for j, product in enumerate(products[1:], 1):
                additional_product_url = product.get('url', product.get('amazon_link', ''))
                if additional_product_url:
                    additional_intro = f"また、{product['name']}も併せてご検討ください。"
                    # まとめ部分の前に挿入
                    if len(modified_sections) > 2:
                        modified_sections.insert(-1, additional_intro)
                        modified_sections.insert(-1, additional_product_url)
                    else:
                        modified_sections.append(additional_intro)
                        modified_sections.append(additional_product_url)
        
        return disclaimer + '\n\n'.join(modified_sections)
    
    def generate_note_tags(self, category: str, article_type: str) -> List[str]:
        """note用のタグを生成"""
        base_tags = self.hashtags_pool.get(category, [])
        article_tags_pool = {
            "レビュー": ["#レビュー", "#体験談", "#口コミ"],
            "ハウツー": ["#ハウツー", "#初心者向け", "#使い方"],
            "商品紹介": ["#おすすめ", "#比較", "#選び方"]
        }
        
        # --- 修正後のロジック ---
        
        # 1. カテゴリに基づいたタグを安全に選択
        #    リストの要素数を超えないように、取得するタグの数を決定
        num_to_select_from_base = min(3, len(base_tags))
        selected_tags = random.sample(base_tags, num_to_select_from_base)
        
        # 2. 記事タイプに基づいたタグを安全に選択
        article_tags = article_tags_pool.get(article_type, [])
        num_to_select_from_article = min(2, len(article_tags))
        
        # 3. 2種類のタグを結合
        if num_to_select_from_article > 0:
            selected_tags.extend(random.sample(article_tags, num_to_select_from_article))
        
        # 4. 重複を削除し、最終的なタグリストを生成 (順序は保持)
        final_tags = list(dict.fromkeys(selected_tags))
        
        # 5. 最大5個のタグを返す
        return final_tags[:5]

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
    
    def generate_complete_article(self, products: List[Dict], article_type: str = None, max_retries: int = 3) -> Dict:
        """完全な記事を生成（タイトル、本文、タグ、X投稿文）"""
        if not article_type:
            article_type = random.choice(self.article_types)
        
        main_product = products[0]
        category = main_product['selected_category']
        
        # 重複チェック機能が有効な場合、複数回試行
        for attempt in range(max_retries):
            logger.info(f"記事生成試行 {attempt + 1}/{max_retries}")
            
            # タイトル生成
            title = self.generate_seo_title(main_product, article_type)
            
            # 記事本文生成
            content = self.generate_article_content(products, article_type, title)
            
            # 重複チェック
            if self.enable_duplicate_check and self.history_manager and self.similarity_analyzer:
                logger.info("記事の重複チェックを実行中...")
                
                # 類似度チェック
                has_similar, similar_articles = self.history_manager.check_similarity(
                    content, similarity_threshold=0.6
                )
                
                if has_similar:
                    logger.warning(f"類似記事を{len(similar_articles)}件発見")
                    for similar in similar_articles[:3]:
                        logger.warning(f"  - {similar['title']} (類似度: {similar['similarity']:.2f})")
                    
                    if attempt < max_retries - 1:
                        logger.info("記事を再生成します...")
                        continue
                    else:
                        logger.warning("最大試行回数に達しました。類似記事が存在しますが、この記事を使用します。")
                else:
                    logger.info("類似記事は見つかりませんでした。記事生成を続行します。")
            
            # アフィリエイトリンク挿入
            final_content = self.insert_affiliate_links(content, products)
            
            # タグ生成
            tags = self.generate_note_tags(category, article_type)
            
            # X投稿パターン生成
            x_patterns = self.generate_x_post_patterns(title, "NOTE_URL_PLACEHOLDER", category)
            
            article_data = {
                "title": title,
                "content": final_content,
                "tags": tags,
                "x_post_patterns": x_patterns,
                "article_type": article_type,
                "category": category,
                "products": products,
                "generated_at": datetime.now().isoformat()
            }
            
            # 記事を履歴に追加
            if self.enable_duplicate_check and self.history_manager:
                try:
                    article_id = self.history_manager.add_article(article_data)
                    logger.info(f"記事を履歴に追加しました (ID: {article_id})")
                except Exception as e:
                    logger.warning(f"記事履歴への追加に失敗: {e}")
            
            return article_data
        
        # ここに到達することはないが、安全のため
        raise RuntimeError("記事生成に失敗しました")
    
    def _get_genre_specific_prompt(self, category: str, product: Dict) -> str:
        """ジャンル別の記事生成プロンプトを取得"""
        genre_prompts = {
            "占い": """
占い・スピリチュアル分野の記事として、以下の観点を含めてください：
- 運気アップや開運効果について
- 使い方や活用方法の具体例
- 初心者でも始めやすい点
- 日常生活への取り入れ方
- 精神的な効果や心の変化
""",
            "フィットネス": """
フィットネス・健康分野の記事として、以下の観点を含めてください：
- 運動効果や健康への影響
- 使用方法やトレーニングのコツ
- 初心者から上級者まで対応できる点
- 継続しやすい工夫や特徴
- 安全性や怪我の予防について
""",
            "書籍": """
書籍・自己啓発分野の記事として、以下の観点を含めてください：
- 内容の要約と学べるポイント
- 実生活への応用方法
- 読みやすさや理解しやすさ
- 他の類似書籍との違い
- 読後の変化や気づき
""",
            "家電・ガジェット": """
家電・ガジェット分野の記事として、以下の観点を含めてください：
- 機能性や性能の詳細
- 使いやすさや操作性
- 省エネ性能やコストパフォーマンス
- 設置や設定の簡単さ
- 他製品との比較や優位性
- 日常生活での便利さ
""",
            "美容・パーソナルケア": """
美容・パーソナルケア分野の記事として、以下の観点を含めてください：
- 美容効果や肌への影響
- 使用感や仕上がりの質感
- 敏感肌でも使えるかどうか
- 時短効果や手軽さ
- 長期使用での変化
- コストパフォーマンス
""",
            "アウトドア・スポーツ": """
アウトドア・スポーツ分野の記事として、以下の観点を含めてください：
- 耐久性や品質の高さ
- 軽量性や携帯性
- 天候や環境への対応力
- 初心者でも使いやすい設計
- 安全性や信頼性
- アウトドア体験の向上効果
""",
            "ヘルスケア・見守り": """
ヘルスケア・見守り分野の記事として、以下の観点を含めてください：
- 健康管理への効果
- 測定精度や信頼性
- 使いやすさや操作の簡単さ
- データ管理や記録機能
- 家族での共有や見守り機能
- 継続的な健康維持への貢献
""",
            "キッチン・時短家事": """
キッチン・時短家事分野の記事として、以下の観点を含めてください：
- 調理時間の短縮効果
- 使いやすさや操作性
- お手入れの簡単さ
- 料理の仕上がりや味
- 収納性やキッチンでの使い勝手
- 家事負担の軽減効果
"""
        }
        
        return genre_prompts.get(category, """
一般的な商品レビューとして、以下の観点を含めてください：
- 商品の特徴や機能
- 使用感や品質
- コストパフォーマンス
- おすすめできる人
- 購入時の注意点
""")

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

