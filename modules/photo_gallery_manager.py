#!/usr/bin/env python3
"""
noteのみんなのフォトギャラリー画像選択・設定モジュール
記事のカテゴリに応じて適切な画像を自動選択し、記事に挿入する機能を提供
"""

import random
import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

class PhotoGalleryManager:
    def __init__(self):
        # カテゴリマッピング：記事カテゴリ → フォトギャラリーカテゴリ
        self.category_mapping = {
            "フィットネス": "人物",
            "健康": "人物", 
            "ダイエット": "人物",
            "料理": "食べ物",
            "グルメ": "食べ物",
            "食品": "食べ物",
            "旅行": "風景",
            "観光": "風景",
            "自然": "風景",
            "書籍": "モノ",
            "学習": "モノ",
            "教育": "モノ",
            "占い": "イラスト",
            "スピリチュアル": "イラスト",
            "アート": "イラスト",
            "都市": "街",
            "建築": "街",
            "ライフスタイル": "すべて",
            "ビジネス": "すべて",
            "テクノロジー": "すべて"
        }
        
        # カテゴリボタンのセレクタマッピング
        self.category_selectors = {
            "すべて": 3,
            "風景": 4,
            "人物": 5,
            "街": 6,
            "モノ": 7,
            "食べ物": 8,
            "イラスト": 9,
            "世界の美術館": 10
        }
    
    def get_photo_category(self, article_category: str) -> str:
        """
        記事カテゴリに基づいて適切なフォトギャラリーカテゴリを取得
        
        Args:
            article_category: 記事のカテゴリ
        
        Returns:
            str: フォトギャラリーのカテゴリ名
        """
        # 完全一致を試行
        if article_category in self.category_mapping:
            return self.category_mapping[article_category]
        
        # 部分一致を試行
        for key, value in self.category_mapping.items():
            if key in article_category or article_category in key:
                return value
        
        # デフォルトは「すべて」
        logger.info(f"カテゴリ '{article_category}' に対応するフォトカテゴリが見つかりません。'すべて'を使用します。")
        return "すべて"
    
    async def open_photo_gallery(self, page: Page) -> bool:
        """
        みんなのフォトギャラリーを開く
        
        Args:
            page: Playwrightのページオブジェクト
        
        Returns:
            bool: 成功した場合True
        """
        try:
            logger.info("みんなのフォトギャラリーを開いています...")
            
            # 画像を追加ボタンをクリック
            await page.wait_for_selector('button[aria-label="画像を追加"]', timeout=10000)
            await page.click('button[aria-label="画像を追加"]')
            
            # 少し待機
            await asyncio.sleep(1)
            
            # 記事にあう画像を選ぶボタンをクリック
            await page.wait_for_selector('button:has-text("記事にあう画像を選ぶ")', timeout=5000)
            await page.click('button:has-text("記事にあう画像を選ぶ")')
            
            # フォトギャラリーの読み込み待機
            await page.wait_for_selector('button:has-text("すべて")', timeout=10000)
            
            logger.info("みんなのフォトギャラリーが正常に開かれました")
            return True
            
        except PlaywrightTimeoutError as e:
            logger.error(f"フォトギャラリーを開く際にタイムアウト: {e}")
            return False
        except Exception as e:
            logger.error(f"フォトギャラリーを開く際にエラー: {e}")
            return False
    
    async def select_category(self, page: Page, category: str) -> bool:
        """
        フォトギャラリーのカテゴリを選択
        
        Args:
            page: Playwrightのページオブジェクト
            category: 選択するカテゴリ名
        
        Returns:
            bool: 成功した場合True
        """
        try:
            if category not in self.category_selectors:
                logger.warning(f"未知のカテゴリ: {category}. 'すべて'を使用します。")
                category = "すべて"
            
            logger.info(f"カテゴリ '{category}' を選択しています...")
            
            # カテゴリボタンをクリック
            category_button = f'button:has-text("{category}")'
            await page.wait_for_selector(category_button, timeout=5000)
            await page.click(category_button)
            
            # 画像の読み込み待機
            await asyncio.sleep(2)
            
            logger.info(f"カテゴリ '{category}' が選択されました")
            return True
            
        except PlaywrightTimeoutError as e:
            logger.error(f"カテゴリ選択でタイムアウト: {e}")
            return False
        except Exception as e:
            logger.error(f"カテゴリ選択でエラー: {e}")
            return False
    
    async def get_available_images(self, page: Page) -> List[int]:
        """
        現在表示されている画像のインデックス一覧を取得
        
        Args:
            page: Playwrightのページオブジェクト
        
        Returns:
            List[int]: 利用可能な画像のインデックス一覧
        """
        try:
            # 画像要素を検索（divでクリエイター名が表示されている要素の前の画像）
            image_elements = await page.query_selector_all('div[style*="cursor: pointer"]')
            
            if not image_elements:
                # 代替方法：画像コンテナを検索
                image_elements = await page.query_selector_all('img[src*="https://"]')
            
            available_indices = []
            
            # 表示されている画像のインデックスを収集
            # noteのフォトギャラリーでは通常12-50程度の画像が表示される
            for i in range(12, 50):  # 一般的な画像インデックス範囲
                try:
                    element = await page.query_selector(f'[data-testid="image-{i}"], img:nth-of-type({i-11})')
                    if element:
                        available_indices.append(i)
                except:
                    continue
            
            # 固定的なインデックス範囲も試行
            if not available_indices:
                available_indices = list(range(12, 35))  # デフォルト範囲
            
            logger.info(f"利用可能な画像数: {len(available_indices)}")
            return available_indices
            
        except Exception as e:
            logger.error(f"画像インデックス取得でエラー: {e}")
            # フォールバック：一般的なインデックス範囲を返す
            return list(range(12, 35))
    
    async def select_random_image(self, page: Page, available_indices: List[int]) -> Optional[int]:
        """
        利用可能な画像からランダムに選択
        
        Args:
            page: Playwrightのページオブジェクト
            available_indices: 利用可能な画像のインデックスリスト
        
        Returns:
            Optional[int]: 選択された画像のインデックス（失敗時はNone）
        """
        if not available_indices:
            logger.error("利用可能な画像がありません")
            return None
        
        try:
            logger.info("画像を選択しています...")
            
            # JavaScriptで画像を確実に選択
            selection_result = await page.evaluate("""
                () => {
                    // 画像コンテナを取得
                    const imageContainers = document.querySelectorAll('figure.sc-a7ee00d5-3');
                    
                    if (imageContainers.length > 3) {
                        const targetImage = imageContainers[3]; // インデックス3（4番目）の画像を選択
                        const rect = targetImage.getBoundingClientRect();
                        
                        console.log('選択する画像の詳細:', {
                            index: 3,
                            className: targetImage.className,
                            cursor: window.getComputedStyle(targetImage).cursor,
                            rect: rect,
                            visible: targetImage.offsetParent !== null
                        });
                        
                        // 画像をクリック
                        targetImage.click();
                        
                        // 選択された画像のURLを取得
                        const img = targetImage.querySelector('img');
                        const imageUrl = img ? img.src : null;
                        
                        return { 
                            success: true, 
                            message: '画像をクリックしました', 
                            index: 3,
                            imageUrl: imageUrl
                        };
                    } else {
                        return { 
                            success: false, 
                            message: '画像が見つかりません',
                            imageUrl: null
                        };
                    }
                }
            """)
            
            if not selection_result['success']:
                logger.error(selection_result['message'])
                return None
            
            logger.info(f"{selection_result['message']} (インデックス: {selection_result['index']})")
            
            # 画像詳細の表示待機
            await asyncio.sleep(2)
            
            # 「この画像を挿入」ボタンの存在確認
            insert_button = await page.query_selector('button:has-text("この画像を挿入")')
            if not insert_button:
                logger.warning("画像挿入ボタンが見つかりません（JavaScriptで検索します）")
            
            logger.info(f"画像 {selection_result['index']} が選択されました")
            return selection_result['index']
            
        except Exception as e:
            logger.error(f"画像選択でエラー: {e}")
            return None
    
    async def insert_selected_image(self, page: Page) -> bool:
        """
        選択された画像を記事に挿入
        
        Args:
            page: Playwrightのページオブジェクト
        
        Returns:
            bool: 成功した場合True
        """
        try:
            logger.info("選択された画像を挿入しています...")
            
            # JavaScriptで黒い「この画像を挿入」ボタンを検索してクリック
            insert_result = await page.evaluate("""
                () => {
                    // 全てのボタンを検索
                    const buttons = document.querySelectorAll('button');
                    let insertButton = null;
                    
                    // テキスト内容で「この画像を挿入」ボタンを探す
                    for (let btn of buttons) {
                        const text = btn.textContent || btn.innerText || '';
                        if (text.includes('この画像を挿入')) {
                            insertButton = btn;
                            break;
                        }
                    }
                    
                    if (insertButton && insertButton.offsetParent !== null) {
                        // ボタンの詳細情報をログ出力
                        const style = window.getComputedStyle(insertButton);
                        console.log('挿入ボタン詳細:', {
                            text: insertButton.textContent,
                            backgroundColor: style.backgroundColor,
                            color: style.color,
                            visible: insertButton.offsetParent !== null
                        });
                        
                        insertButton.click();
                        return { success: true, message: '黒い画像挿入ボタンをクリックしました' };
                    } else {
                        return { success: false, message: '画像挿入ボタンが見つかりません' };
                    }
                }
            """)
            
            if not insert_result['success']:
                logger.error(insert_result['message'])
                return False
            
            logger.info(insert_result['message'])
            
            # 画像サイズ調整ダイアログの表示待機
            try:
                await page.wait_for_selector('button:has-text("保存")', timeout=10000)
                logger.info("画像サイズ調整ダイアログが表示されました")
                
                # 少し待機してから保存
                await asyncio.sleep(1)
                
                # 保存ボタンをクリック
                await page.click('button:has-text("保存")')
                logger.info("画像サイズ調整を保存しました")
                
            except PlaywrightTimeoutError:
                logger.warning("画像サイズ調整ダイアログが表示されませんでした（直接挿入された可能性があります）")
            
            # 画像挿入完了の待機
            await asyncio.sleep(3)
            
            logger.info("画像が正常に挿入されました")
            return True
            
        except PlaywrightTimeoutError as e:
            logger.error(f"画像挿入でタイムアウト: {e}")
            return False
        except Exception as e:
            logger.error(f"画像挿入でエラー: {e}")
            return False
    
    async def add_photo_to_article(self, page: Page, article_category: str) -> bool:
        """
        記事に適切な画像を自動追加
        
        Args:
            page: Playwrightのページオブジェクト
            article_category: 記事のカテゴリ
        
        Returns:
            bool: 成功した場合True
        """
        try:
            logger.info(f"記事カテゴリ '{article_category}' に基づいて画像を追加します")
            
            # 1. フォトギャラリーを開く
            if not await self.open_photo_gallery(page):
                return False
            
            # 2. 適切なカテゴリを選択
            photo_category = self.get_photo_category(article_category)
            if not await self.select_category(page, photo_category):
                return False
            
            # 3. 利用可能な画像を取得
            available_images = await self.get_available_images(page)
            if not available_images:
                logger.error("利用可能な画像が見つかりません")
                return False
            
            # 4. ランダムに画像を選択
            selected_image = await self.select_random_image(page, available_images)
            if selected_image is None:
                return False
            
            # 5. 選択された画像を挿入
            if not await self.insert_selected_image(page):
                return False
            
            logger.info("記事への画像追加が完了しました")
            return True
            
        except Exception as e:
            logger.error(f"記事への画像追加でエラー: {e}")
            return False

# 使用例とテスト
if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # PhotoGalleryManagerのインスタンス作成
    photo_manager = PhotoGalleryManager()
    
    # カテゴリマッピングのテスト
    test_categories = ["フィットネス", "料理", "旅行", "書籍", "占い", "未知のカテゴリ"]
    
    print("=== カテゴリマッピングテスト ===")
    for category in test_categories:
        photo_category = photo_manager.get_photo_category(category)
        print(f"記事カテゴリ: {category} → フォトカテゴリ: {photo_category}")
    
    print("\n=== 利用可能なフォトカテゴリ ===")
    for category in photo_manager.category_selectors.keys():
        print(f"- {category}")
    
    print("\nPhotoGalleryManagerの初期化が完了しました")

