# noteの正しい画像挿入手順

## 成功した手順
1. ✅ 「画像を追加」ボタンをクリック
2. ✅ 「記事にあう画像を選ぶ」ボタンをクリック
3. ✅ カテゴリ（例：「モノ」）を選択
4. ✅ 画像を選択（右側に詳細パネルが表示される）
5. ✅ **黒い「この画像を挿入」ボタンをJavaScriptで検索・クリック**
6. ✅ 画像サイズ調整ダイアログで「保存」ボタンをクリック

## 重要な発見
- **「この画像を挿入」ボタンは黒いボタン（背景色: rgb(8, 19, 26)）**
- ボタンはDOM内のインデックス67に位置していた
- 通常のPlaywrightセレクタでは検出困難
- JavaScriptによる直接検索・クリックが必要

## 成功したJavaScriptコード
```javascript
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
    insertButton.click();
    return { success: true, message: '画像挿入ボタンをクリックしました' };
}
```

## 結果
- 画像が記事の上部に正常に挿入された
- 書籍売り場の画像が表示されている
- クリエイター情報も適切に表示されている（Photo by satoshi_st）

## 修正が必要なコード
PhotoGalleryManagerの`insert_selected_image`メソッドは既に正しいJavaScript検索方式を実装済みですが、実際のテストで動作確認が必要です。

