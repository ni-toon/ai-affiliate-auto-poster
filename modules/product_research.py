"""
商品リサーチモジュール（拡張版）
多様な分野の人気商品をリサーチし、
Amazonアソシエイトリンクを生成する機能を提供
"""

import random
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlparse, parse_qs, urlencode, urlunparse
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
            ],
            "家電・ガジェット": [
                {
                    "name": "ワイヤレスイヤホン Bluetooth5.3",
                    "category": "オーディオ機器",
                    "keywords": ["ワイヤレスイヤホン", "Bluetooth", "ノイズキャンセリング"],
                    "price_range": "5000-15000",
                    "description": "高音質でノイズキャンセリング機能付きのワイヤレスイヤホン"
                },
                {
                    "name": "スマートフォン 急速充電器 65W",
                    "category": "充電器",
                    "keywords": ["急速充電器", "USB-C", "PD対応"],
                    "price_range": "2000-5000",
                    "description": "USB-C PD対応の高速充電器でスマホを素早く充電"
                },
                {
                    "name": "ロボット掃除機 自動充電",
                    "category": "掃除機",
                    "keywords": ["ロボット掃除機", "自動充電", "スマート"],
                    "price_range": "20000-50000",
                    "description": "自動充電機能付きで賢く掃除するロボット掃除機"
                },
                {
                    "name": "空気清浄機 HEPA フィルター",
                    "category": "空調家電",
                    "keywords": ["空気清浄機", "HEPA", "花粉対策"],
                    "price_range": "10000-30000",
                    "description": "HEPAフィルター搭載で花粉やPM2.5を除去する空気清浄機"
                },
                {
                    "name": "電気圧力鍋 4L 自動調理",
                    "category": "調理家電",
                    "keywords": ["電気圧力鍋", "自動調理", "時短"],
                    "price_range": "8000-20000",
                    "description": "ボタン一つで本格料理が作れる電気圧力鍋"
                },
                {
                    "name": "Wi-Fi 6 ルーター 高速通信",
                    "category": "ネットワーク機器",
                    "keywords": ["Wi-Fi6", "ルーター", "高速通信"],
                    "price_range": "8000-25000",
                    "description": "最新Wi-Fi 6対応で高速インターネット通信を実現"
                }
            ],
            "美容・パーソナルケア": [
                {
                    "name": "ドライヤー マイナスイオン 大風量",
                    "category": "ヘアケア",
                    "keywords": ["ドライヤー", "マイナスイオン", "大風量"],
                    "price_range": "5000-15000",
                    "description": "マイナスイオンで髪をサラサラに仕上げる大風量ドライヤー"
                },
                {
                    "name": "電動歯ブラシ 音波振動",
                    "category": "オーラルケア",
                    "keywords": ["電動歯ブラシ", "音波振動", "歯垢除去"],
                    "price_range": "3000-10000",
                    "description": "音波振動で効果的に歯垢を除去する電動歯ブラシ"
                },
                {
                    "name": "美顔器 RF温熱 EMS",
                    "category": "美容機器",
                    "keywords": ["美顔器", "RF", "EMS", "リフトアップ"],
                    "price_range": "8000-25000",
                    "description": "RF温熱とEMSでリフトアップ効果が期待できる美顔器"
                },
                {
                    "name": "プロテイン ホエイ 美容成分配合",
                    "category": "サプリメント",
                    "keywords": ["プロテイン", "美容", "コラーゲン"],
                    "price_range": "3000-8000",
                    "description": "美容成分配合で内側からキレイをサポートするプロテイン"
                },
                {
                    "name": "ヘアアイロン ストレート カール 2way",
                    "category": "ヘアケア",
                    "keywords": ["ヘアアイロン", "ストレート", "カール"],
                    "price_range": "3000-12000",
                    "description": "ストレートもカールも自在に作れる2wayヘアアイロン"
                },
                {
                    "name": "スキンケア セット 保湿",
                    "category": "スキンケア",
                    "keywords": ["スキンケア", "保湿", "美容液"],
                    "price_range": "3000-10000",
                    "description": "保湿効果の高いスキンケアセットで美肌をキープ"
                }
            ],
            "アウトドア・スポーツ": [
                {
                    "name": "テント 2人用 軽量 防水",
                    "category": "キャンプ用品",
                    "keywords": ["テント", "2人用", "軽量", "防水"],
                    "price_range": "8000-20000",
                    "description": "軽量で防水性に優れた2人用テント"
                },
                {
                    "name": "ランニングシューズ クッション性",
                    "category": "スポーツシューズ",
                    "keywords": ["ランニングシューズ", "クッション", "軽量"],
                    "price_range": "5000-15000",
                    "description": "クッション性に優れた軽量ランニングシューズ"
                },
                {
                    "name": "登山リュック 40L 軽量",
                    "category": "登山用品",
                    "keywords": ["登山リュック", "40L", "軽量", "防水"],
                    "price_range": "8000-20000",
                    "description": "軽量で機能性に優れた40L登山リュック"
                },
                {
                    "name": "キャンプチェア 軽量 コンパクト",
                    "category": "キャンプ用品",
                    "keywords": ["キャンプチェア", "軽量", "コンパクト"],
                    "price_range": "3000-8000",
                    "description": "持ち運びやすい軽量コンパクトなキャンプチェア"
                },
                {
                    "name": "スポーツウォッチ GPS機能",
                    "category": "スポーツ用品",
                    "keywords": ["スポーツウォッチ", "GPS", "ランニング"],
                    "price_range": "10000-30000",
                    "description": "GPS機能付きでランニングやトレーニングをサポート"
                },
                {
                    "name": "クーラーボックス 大容量",
                    "category": "キャンプ用品",
                    "keywords": ["クーラーボックス", "大容量", "保冷"],
                    "price_range": "5000-15000",
                    "description": "大容量で長時間保冷できるクーラーボックス"
                }
            ],
            "ヘルスケア・見守り": [
                {
                    "name": "体組成計 Bluetooth対応",
                    "category": "健康機器",
                    "keywords": ["体組成計", "Bluetooth", "スマホ連携"],
                    "price_range": "3000-8000",
                    "description": "Bluetooth対応でスマホと連携できる高機能体組成計"
                },
                {
                    "name": "血圧計 上腕式 自動測定",
                    "category": "健康機器",
                    "keywords": ["血圧計", "上腕式", "自動測定"],
                    "price_range": "5000-12000",
                    "description": "正確な測定ができる上腕式自動血圧計"
                },
                {
                    "name": "睡眠グッズ アイマスク 耳栓セット",
                    "category": "睡眠用品",
                    "keywords": ["睡眠", "アイマスク", "耳栓"],
                    "price_range": "1000-3000",
                    "description": "快適な睡眠をサポートするアイマスクと耳栓のセット"
                },
                {
                    "name": "マッサージガン 筋膜リリース",
                    "category": "マッサージ機器",
                    "keywords": ["マッサージガン", "筋膜リリース", "疲労回復"],
                    "price_range": "5000-15000",
                    "description": "筋膜リリースで疲労回復をサポートするマッサージガン"
                },
                {
                    "name": "パルスオキシメータ 血中酸素濃度",
                    "category": "健康機器",
                    "keywords": ["パルスオキシメータ", "血中酸素", "健康管理"],
                    "price_range": "2000-5000",
                    "description": "血中酸素濃度を簡単に測定できるパルスオキシメータ"
                },
                {
                    "name": "体温計 非接触式 デジタル",
                    "category": "健康機器",
                    "keywords": ["体温計", "非接触", "デジタル"],
                    "price_range": "2000-6000",
                    "description": "非接触で素早く正確に体温を測定できるデジタル体温計"
                }
            ],
            "キッチン・時短家事": [
                {
                    "name": "フライパン セット IH対応",
                    "category": "調理器具",
                    "keywords": ["フライパン", "セット", "IH対応"],
                    "price_range": "3000-10000",
                    "description": "IH対応で使いやすいフライパンセット"
                },
                {
                    "name": "真空保存容器 セット",
                    "category": "保存容器",
                    "keywords": ["真空保存", "容器", "食材保存"],
                    "price_range": "2000-6000",
                    "description": "食材を新鮮に保つ真空保存容器セット"
                },
                {
                    "name": "食洗機用洗剤 大容量",
                    "category": "洗剤",
                    "keywords": ["食洗機", "洗剤", "大容量"],
                    "price_range": "1000-3000",
                    "description": "食洗機専用の高性能洗剤大容量タイプ"
                },
                {
                    "name": "コーヒーメーカー 全自動",
                    "category": "調理家電",
                    "keywords": ["コーヒーメーカー", "全自動", "ドリップ"],
                    "price_range": "8000-25000",
                    "description": "豆から挽いて淹れる全自動コーヒーメーカー"
                },
                {
                    "name": "電気ケトル 温度調節機能",
                    "category": "調理家電",
                    "keywords": ["電気ケトル", "温度調節", "保温"],
                    "price_range": "3000-8000",
                    "description": "温度調節機能付きで様々な用途に使える電気ケトル"
                },
                {
                    "name": "包丁セット ステンレス",
                    "category": "調理器具",
                    "keywords": ["包丁", "セット", "ステンレス"],
                    "price_range": "5000-15000",
                    "description": "切れ味抜群のステンレス製包丁セット"
                }
            ]
        }

        # ジャンル別の画像カテゴリマッピング
        self.image_category_mapping = {
            "占い": "モノ",
            "フィットネス": "人物",
            "書籍": "モノ",
            "家電・ガジェット": "モノ",
            "美容・パーソナルケア": "モノ",
            "アウトドア・スポーツ": "風景",
            "ヘルスケア・見守り": "モノ",
            "キッチン・時短家事": "食べ物"
        }

    # =========================
    # 日本向けリンク正規化
    # =========================
    def _to_jp_affiliate_link(self, base: str) -> str:
        """
        任意の Amazon URL / 'SEARCH:<query>' を、
        日本リージョンで確実に開けるリンクに正規化し、tag を必ず付ける。
        """
        if not base:
            return ""

        # 検索指定（SEARCH: クエリ）
        if base.startswith("SEARCH:"):
            q = base.split(":", 1)[1].strip()
            return f"https://www.amazon.co.jp/s?k={quote(q)}&tag={self.amazon_associate_id}&language=ja_JP"

        # URLでない場合は検索にフォールバック
        if not base.startswith("http"):
            q = base.strip()
            return f"https://www.amazon.co.jp/s?k={quote(q)}&tag={self.amazon_associate_id}&language=ja_JP"

        # URLを amazon.co.jp に正規化し、tag/language を追加
        p = list(urlparse(base))
        p[0] = "https"
        p[1] = "www.amazon.co.jp"  # netloc を日本に固定
        q = parse_qs(p[4])
        q["tag"] = [self.amazon_associate_id]  # 既存があっても上書き
        q.setdefault("language", ["ja_JP"])
        p[4] = urlencode({k: v[0] if isinstance(v, list) else v for k, v in q.items()})
        return urlunparse(p)

    def get_random_product(self, category: str = None) -> Dict:
        """指定されたカテゴリまたはランダムなカテゴリから商品を選択"""
        if category and category in self.categories:
            selected_category = category
        else:
            selected_category = random.choice(list(self.categories.keys()))

        product = random.choice(self.categories[selected_category])
        product["selected_category"] = selected_category
        return product

    def get_image_category(self, genre: str) -> str:
        """ジャンルに対応する画像カテゴリを取得"""
        return self.image_category_mapping.get(genre, "モノ")

    def get_available_genres(self) -> List[str]:
        """利用可能なジャンル一覧を取得"""
        return list(self.categories.keys())

    def generate_amazon_link(self, product_name: str, keywords: List[str] = None) -> str:
        """
        商品名とキーワードからAmazonアソシエイトリンクを生成（日本リージョン保証）
        - 安定ASIN（書籍など）は日本のDPリンク
        - 型番が流動/汎用品は 'SEARCH:' で日本検索リンクへ
        - どの場合も tag / language=ja_JP を必ず付与
        """
        product_mappings = {
            # --- 占い：版分岐が多いため検索に統一 ---
            "ゲッターズ飯田の五星三心占い2024完全版": "SEARCH:ゲッターズ飯田 五星三心 2024",
            "タロットカード 初心者向けセット": "SEARCH:タロットカード 初心者 セット",
            "78枚のカードで占う、いちばんていねいなタロット": "SEARCH:78枚のカードで占う いちばんていねいなタロット 書籍",
            "パワーストーン ブレスレット": "SEARCH:パワーストーン ブレスレット",
            "風水開運グッズセット": "SEARCH:風水 開運 グッズ セット",

            # --- フィットネス：ブランドや在庫変動が大きいので検索へ ---
            "STEADY フィットネスバイク エアロバイク": "SEARCH:STEADY エアロバイク",
            "可変式ダンベル セット": "SEARCH:可変式 ダンベル セット",
            "腹筋ローラー": "SEARCH:腹筋ローラー",
            "レジスタンスバンド セット": "SEARCH:レジスタンスバンド セット",
            "ヨガマット": "SEARCH:ヨガマット 厚手",
            "プロテイン ホエイ": "SEARCH:ホエイ プロテイン 1kg",

            # --- 書籍：安定DPに更新（日本） ---
            "嫌われる勇気": "https://www.amazon.co.jp/dp/4478025819",
            "変な家2 ～11の間取り図～": "https://www.amazon.co.jp/dp/4864109826",
            "ハーバード、スタンフォード、オックスフォード… 科学的に証明された すごい習慣大百科": "https://www.amazon.co.jp/dp/B0FFZ73L7F",
            "世界の一流は「雑談」で何を話しているのか": "https://www.amazon.co.jp/dp/4295408107",
            "DIE WITH ZERO 人生が豊かになりすぎる究極のルール": "https://www.amazon.co.jp/dp/4478109680",
            "改訂版 本当の自由を手に入れる お金の大学": "https://www.amazon.co.jp/dp/4023323780",

            # --- 家電・ガジェット：型番流動のため検索へ ---
            "ワイヤレスイヤホン Bluetooth5.3": "SEARCH:ワイヤレスイヤホン Bluetooth5.3",
            "スマートフォン 急速充電器 65W": "SEARCH:急速充電器 65W USB-C GaN",
            "ロボット掃除機 自動充電": "SEARCH:ロボット掃除機 自動充電",
            "空気清浄機 HEPA フィルター": "SEARCH:空気清浄機 HEPA フィルター",
            "電気圧力鍋 4L 自動調理": "SEARCH:電気圧力鍋 4L",
            "Wi-Fi 6 ルーター 高速通信": "SEARCH:Wi-Fi 6 ルーター"
        }

        base = product_mappings.get(product_name)

        if base:
            return self._to_jp_affiliate_link(base)

        # マッピングが無い → キーワードまたは商品名で日本検索
        search_query = " ".join(keywords[:2]) if keywords else product_name
        return f"https://www.amazon.co.jp/s?k={quote(search_query)}&tag={self.amazon_associate_id}&language=ja_JP"

    def search_amazon_products(self, query: str, max_results: int = 5) -> List[Dict]:
        """Amazon検索結果から商品情報を取得（簡易版：カテゴリデータから擬似的に返す）"""
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

    def get_products_for_article(self, genre: str, num_products: int = 3) -> List[Dict]:
        """記事用の商品リストを取得（日本リンク保証版）"""
        if genre not in self.categories:
            # 指定されたジャンルがない場合はランダムに選択
            genre = random.choice(list(self.categories.keys()))

        products = self.categories[genre]

        # 指定された数の商品をランダムに選択
        if len(products) <= num_products:
            selected_products_base = products.copy()
        else:
            selected_products_base = random.sample(products, num_products)

        # 選択された各商品にジャンル情報とAmazonリンクを追加
        selected_products = []
        for product in selected_products_base:
            product_copy = product.copy()  # 元のデータを変更しないようにコピーを作成
            product_copy["selected_category"] = genre  # ★ジャンル情報を追加
            product_copy["amazon_link"] = self.generate_amazon_link(
                product_copy["name"],
                product_copy["keywords"]
            )
            selected_products.append(product_copy)

        return selected_products


if __name__ == "__main__":
    # テスト実行
    researcher = ProductResearcher()

    print("=== 利用可能なジャンル ===")
    for genre in researcher.get_available_genres():
        print(f"- {genre}")

    print("\n=== 各ジャンルのサンプル商品 ===")
    for genre in researcher.get_available_genres():
        product = researcher.get_random_product(genre)
        print(f"\n【{genre}】")
        print(f"商品名: {product['name']}")
        print(f"価格帯: {product['price_range']}円")
        print(f"説明: {product['description']}")
        print(f"画像カテゴリ: {researcher.get_image_category(genre)}")

    # 動作確認：日本リンク生成例
    print("\n=== リンク生成チェック ===")
    for name in ["嫌われる勇気", "可変式ダンベル セット", "ワイヤレスイヤホン Bluetooth5.3"]:
        print(name, "=>", researcher.generate_amazon_link(name, ["テスト", "キーワード"]))
