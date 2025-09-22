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
            # 既存のカテゴリ
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
            "占い": "モノ",
            "スピリチュアル": "イラスト",
            "アート": "イラスト",
            "都市": "街",
            "建築": "街",
            "ライフスタイル": "すべて",
            "ビジネス": "すべて",
            "テクノロジー": "すべて",
            
            # 新規追加ジャンル
            "家電・ガジェット": "モノ",
            "PC・自作・周辺": "モノ",
            "写真・動画・クリエイティブ": "モノ",
            "ゲーム・オタク向け": "モノ",
            "美容・パーソナルケア": "モノ",
            "ヘルスケア・見守り": "モノ",
            "キッチン・時短家事": "食べ物",
            "収納・インテリア・在宅": "モノ",
            "ベビー・キッズ・知育": "モノ",
            "ペット": "モノ",
            "アウトドア・スポーツ": "風景",
            "防災・季節商材": "モノ",
            "カー・バイク": "モノ",
            "DIY・工具・日曜大工": "モノ",
            "文房具・オフィス": "モノ",
            "音楽・DTM": "モノ"
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
    
    # photo_gallery_manager.py

# ... (他のメソッドはそのまま) ...

# ▼▼▼ select_random_image メソッドをこちらに置き換えてください ▼▼▼
    async def select_random_image(self, page: Page, available_indices: List[int]) -> Optional[int]:
        """
        利用可能な画像からランダムに1つ選択し、クリックする。
        
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
            
            # 複数の画像コンテナを特定するセレクタ
            # note.comのUIでは figure タグで画像が囲まれていることが多い
            image_selector = "figure.sc-a7ee00d5-3"
            
            # 画像が表示されるまで待機
            await page.wait_for_selector(image_selector, state="visible", timeout=10000)
            
            # すべての画像要素を取得
            images = await page.query_selector_all(image_selector)
            
            if not images:
                logger.error("クリック対象の画像要素が見つかりません。")
                return None
                
            # 4番目の画像を選択（インデックス3）。リストの範囲外にならないようにチェック
            image_index_to_click = 3
            if len(images) <= image_index_to_click:
                logger.warning(f"画像の数が足りないため、最後の画像（インデックス: {len(images) - 1}）を選択します。")
                image_index_to_click = len(images) - 1

            # 選択した画像をクリック
            target_image = images[image_index_to_click]
            await target_image.click()
            
            logger.info(f"画像をクリックしました (インデックス: {image_index_to_click})")
            
            # 画像詳細（「次へ」ボタンなど）が表示されるのを待つ
            await page.wait_for_timeout(1500)
            
            return image_index_to_click

        except PlaywrightTimeoutError:
            logger.error("画像コンテナの表示待機中にタイムアウトしました。")
            return None
        except Exception as e:
            logger.error(f"画像選択で予期せぬエラー: {e}")
            return None

    # ▼▼▼ insert_selected_image メソッドをこちらに置き換えてください ▼▼▼
    async def insert_selected_image(self, page: Page) -> bool:
        """
        選択された画像を記事に挿入するまでの一連のボタンクリックを処理する。
        
        Args:
            page: Playwrightのページオブジェクト
        
        Returns:
            bool: 成功した場合True
        """
        try:

            # --- ステップ2: 「この画像を挿入」ボタンをクリック ---
            logger.info("「この画像を挿入」ボタンを探しています...")
            insert_button = page.get_by_role("button", name="この画像を挿入")
            await insert_button.wait_for(state="visible", timeout=10000)
            await insert_button.click()
            logger.info("「この画像を挿入」ボタンをクリックしました。")

            # --- ステップ3: 画像サイズ調整ダイアログの「保存」ボタンをクリック ---
            logger.info("画像サイズ調整ダイアログの「保存」ボタンを探しています...")
            # ダイアログ（モーダル）内のボタンとして特定
            save_button = page.locator('[role="dialog"]').get_by_role("button", name="保存")
            await save_button.wait_for(state="visible", timeout=10000)
            await save_button.click()
            logger.info("画像サイズ調整ダイアログの「保存」ボタンをクリックしました。")

            # 記事エディタに画像が挿入されるのを待つ
            await page.wait_for_timeout(2000)
            logger.info("画像が正常に記事へ挿入されました。")
            
            return True

        except PlaywrightTimeoutError as e:
            logger.error(f"ボタンの待機中にタイムアウトしました: {e.message}")
            # タイムアウト時にスクリーンショットを撮り、デバッグに役立てる
            await page.screenshot(path="error_screenshot_button_timeout.png")
            logger.info("タイムアウト時のスクリーンショットを 'error_screenshot_button_timeout.png' として保存しました。")
            return False
        except Exception as e:
            logger.error(f"画像挿入プロセスで予期せぬエラー: {e}")
            await page.screenshot(path="error_screenshot_unexpected.png")
            logger.info("予期せぬエラー時のスクリーンショットを 'error_screenshot_unexpected.png' として保存しました。")
            return False

# ... (以降のメソッドはそのまま) ...

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
            
            # 画像サイズ調整ダイアログの表示待機と保存ボタンクリック
            try:
                # 保存ボタンの表示待機
                await page.wait_for_selector('button:has-text("保存")', timeout=10000)
                logger.info("画像サイズ調整ダイアログが表示されました")
                
                # 少し待機してから保存
                await asyncio.sleep(1)
                
                # 方法1: ダイアログ内の保存ボタンを正確に特定してクリック
                save_result = await page.evaluate("""
                    () => {
                        // ダイアログ内の保存ボタンを特定
                        const dialog = document.querySelector('[role="dialog"]') || 
                                       document.querySelector('.modal') ||
                                       document.querySelector('[aria-modal="true"]') ||
                                       document.querySelector('div[style*="position: fixed"]');
                        
                        if (dialog) {
                            const saveButtons = dialog.querySelectorAll('button');
                            for (let btn of saveButtons) {
                                const text = btn.textContent || btn.innerText || '';
                                if (text.includes('保存') && btn.offsetParent !== null) {
                                    console.log('ダイアログ内の保存ボタンを発見:', {
                                        text: text,
                                        rect: btn.getBoundingClientRect()
                                    });
                                    btn.click();
                                    return { success: true, message: 'ダイアログ内の保存ボタンをクリックしました' };
                                }
                            }
                        }
                        
                        // 方法2: 全ボタンから画像サイズ調整ダイアログの保存ボタンを特定
                        const allButtons = document.querySelectorAll('button');
                        let dialogSaveButton = null;
                        
                        for (let btn of allButtons) {
                            const text = btn.textContent || btn.innerText || '';
                            const rect = btn.getBoundingClientRect();
                            
                            // 画像サイズ調整ダイアログの保存ボタンの特徴
                            // - テキストが「保存」
                            // - 画面の中央下部に位置
                            // - 「下書き保存」ではない
                            if (text === '保存' && 
                                rect.y > 500 && 
                                rect.x > 600 && 
                                btn.offsetParent !== null) {
                                dialogSaveButton = btn;
                                break;
                            }
                        }
                        
                        if (dialogSaveButton) {
                            console.log('画像サイズ調整ダイアログの保存ボタンを発見:', {
                                text: dialogSaveButton.textContent,
                                rect: dialogSaveButton.getBoundingClientRect()
                            });
                            dialogSaveButton.click();
                            return { success: true, message: '画像サイズ調整ダイアログの保存ボタンをクリックしました' };
                        }
                        
                        return { success: false, message: '画像サイズ調整ダイアログの保存ボタンが見つかりません' };
                    }
                """)
                
                if save_result['success']:
                    logger.info(save_result['message'])
                else:
                    logger.error(save_result['message'])
                    # フォールバック：インデックス指定でクリック
                    try:
                        # 画像サイズ調整ダイアログが表示されている場合、通常インデックス3が保存ボタン
                        await page.click('button >> nth=2')  # 3番目のボタン（0ベース）
                        logger.info("インデックス指定で保存ボタンをクリックしました")
                    except Exception as e:
                        logger.error(f"インデックス指定保存ボタンクリックでエラー: {e}")
                        # 最終フォールバック：座標クリック
                        try:
                            await page.click('css=body', position={'x': 760, 'y': 623})
                            logger.info("座標指定で保存ボタンをクリックしました")
                        except Exception as e2:
                            logger.error(f"座標指定保存ボタンクリックでエラー: {e2}")
                            return False
                
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

