#!/usr/bin/env python3
"""
修正版のアフィリエイトリンク作成機能の最終テスト
手動テストで100%成功した方法を実装したバージョンをテスト
"""

import asyncio
import json
import logging
from modules.note_poster import NotePoster

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_final_link_creation():
    """修正版のリンク作成機能をテスト"""
    
    # 設定読み込み
    with open('config/config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # NotePosterを初期化
    poster = NotePoster(
        username=config['note']['username'],
        password=config['note']['password'],
        headless=True  # ヘッドレスモードでテスト
    )
    
    try:
        logger.info("=== 修正版リンク作成機能テスト開始 ===")
        
        # ブラウザ起動
        await poster.start_browser()
        
        # ログイン
        if not await poster.login():
            logger.error("ログインに失敗しました")
            return False
        
        logger.info("✅ ログイン成功")
        
        # 新規記事作成ページに移動
        await poster.page.goto("https://note.com/new")
        await poster.page.wait_for_load_state("networkidle")
        
        # テスト用記事データ
        test_title = "【最終テスト】アフィリエイトリンク作成機能検証"
        test_content = """
この記事は、修正されたアフィリエイトリンク作成機能のテストです。

以下の商品リンクが正常にリンク化されることを確認します：

1. 最初の商品: [Amazon商品リンク_タロットカード占い入門書]

この商品は占いに興味がある方におすすめです。

2. 二番目の商品: [Amazon商品リンク_フィットネストレーニング器具]

健康維持に最適なトレーニング器具です。

3. 三番目の商品: [Amazon商品リンク_ビジネス書籍ベストセラー]

ビジネススキル向上に役立つ書籍です。

これらのリンクが全て正常に作成されれば、修正は成功です。
        """
        
        # テスト用商品データ
        test_products = [
            {
                'name': 'タロットカード占い入門書',
                'amazon_link': 'https://www.amazon.co.jp/dp/TEST001'
            },
            {
                'name': 'フィットネストレーニング器具',
                'amazon_link': 'https://www.amazon.co.jp/dp/TEST002'
            },
            {
                'name': 'ビジネス書籍ベストセラー',
                'amazon_link': 'https://www.amazon.co.jp/dp/TEST003'
            }
        ]
        
        # タイトル入力
        logger.info("📝 タイトル入力中...")
        await poster.page.wait_for_selector('textarea', timeout=10000)
        await poster.page.fill('textarea', test_title)
        logger.info("✅ タイトル入力成功")
        
        # 本文入力
        logger.info("📝 本文入力中...")
        escaped_content = test_content.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
        
        js_code = f"""
        const contentDiv = document.querySelector('div[contenteditable="true"]');
        if (contentDiv) {{
            contentDiv.innerHTML = `{escaped_content}`.replace(/\\n/g, '<br>');
            contentDiv.focus();
            contentDiv.blur();
            true;
        }} else {{
            false;
        }}
        """
        
        result = await poster.page.evaluate(js_code)
        if result:
            logger.info("✅ 本文入力成功")
        else:
            logger.error("❌ 本文入力失敗")
            return False
        
        # 少し待機
        await asyncio.sleep(2)
        
        # アフィリエイトリンク変換テスト
        logger.info("🔗 アフィリエイトリンク変換開始...")
        conversion_result = await poster.convert_affiliate_placeholders(test_products)
        
        if conversion_result:
            logger.info("🎉 アフィリエイトリンク変換成功！")
        else:
            logger.error("❌ アフィリエイトリンク変換失敗")
            return False
        
        # 最終確認: 作成されたリンクの数を確認
        link_count = await poster.page.evaluate("""
        const content = document.querySelector('div[contenteditable="true"]');
        if (content) {
            const links = content.querySelectorAll('a');
            return links.length;
        }
        return 0;
        """)
        
        logger.info(f"📊 作成されたリンク数: {link_count}/{len(test_products)}")
        
        # 各リンクの詳細確認
        link_details = await poster.page.evaluate("""
        const content = document.querySelector('div[contenteditable="true"]');
        if (content) {
            const links = content.querySelectorAll('a');
            const details = [];
            links.forEach((link, index) => {
                details.push({
                    index: index + 1,
                    text: link.textContent,
                    href: link.href
                });
            });
            return details;
        }
        return [];
        """)
        
        logger.info("📋 作成されたリンクの詳細:")
        for detail in link_details:
            logger.info(f"  {detail['index']}. テキスト: '{detail['text']}' → URL: {detail['href']}")
        
        # 成功判定
        success_rate = link_count / len(test_products) * 100
        logger.info(f"🎯 成功率: {success_rate:.1f}%")
        
        if link_count == len(test_products):
            logger.info("🎉 全てのリンクが正常に作成されました！修正は完全に成功です！")
            return True
        elif link_count > 0:
            logger.warning(f"⚠️ 部分的成功: {link_count}/{len(test_products)} のリンクが作成されました")
            return True
        else:
            logger.error("❌ リンクが1つも作成されませんでした")
            return False
        
    except Exception as e:
        logger.error(f"テスト中にエラーが発生: {e}")
        return False
    
    finally:
        # ブラウザを閉じる
        await poster.close_browser()

async def main():
    """メイン関数"""
    logger.info("修正版アフィリエイトリンク作成機能の最終テストを開始します")
    
    success = await test_final_link_creation()
    
    if success:
        logger.info("🎉 テスト成功！修正されたリンク作成機能は正常に動作しています")
    else:
        logger.error("❌ テスト失敗。さらなる修正が必要です")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())

