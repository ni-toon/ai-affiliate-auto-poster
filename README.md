# AI Affiliate Auto Poster

AIによるアフィリエイト記事の自動生成からnote投稿、X投稿までを完全自動化するシステムです。

## 概要

このシステムは、以下の機能を自動で実行します。

1.  **記事生成**:
    *   ジャンル（レビュー、ハウツー、商品紹介）と商品カテゴリ（占い、フィットネス、書籍）をランダムに選択。
    *   OpenAI API (GPT-4o mini) を使用して、500〜1000文字程度の記事を自動生成。
    *   記事構成：「概要 → メリット → デメリット → まとめ」。
    *   冒頭に「※本記事にはアフィリエイトリンクを含みます」と記載。
    *   Amazonアソシエイトリンクを本文中に自然に挿入。

2.  **note投稿**:
    *   生成した記事をnoteに自動投稿。
    *   SEOを意識したタイトルを自動生成。
    *   noteタグを3〜5個自動付与。

3.  **X投稿**:
    *   note投稿完了後、X（旧Twitter）へ自動で宣伝投稿。
    *   投稿文は「記事タイトル＋短縮URL＋ハッシュタグ」の形式。
    *   投稿文は複数のパターンからランダムに選択。

4.  **スケジューリング**:
    *   1日5記事を、指定された時間帯（デフォルトは9:00〜21:00）にランダムな間隔で自動投稿。

## システム構成

*   **言語**: Python 3.11
*   **主要ライブラリ**:
    *   `openai`: 記事生成
    *   `playwright`: ブラウザ自動操作（note, Xへの投稿）
    *   `schedule`: タスクスケジューリング
    *   `beautifulsoup4`: 商品リサーチ（補助）
*   **ディレクトリ構造**:
    ```
    ai-affiliate-auto-poster/
    ├── src/                    # ソースコード
    │   ├── main_controller.py  # メインコントローラー
    │   └── scheduler.py        # スケジューラー
    ├── modules/                # 各機能モジュール
    │   ├── product_research.py # 商品リサーチ
    │   ├── article_generator.py# AI記事生成
    │   ├── note_poster.py      # note投稿
    │   └── x_poster.py         # X投稿
    ├── config/                 # 設定ファイル
    │   ├── config.json.template# 設定ファイルテンプレート
    │   └── config.json         # 各種設定（作成後）
    ├── data/                   # 生成データ
    │   ├── generated_articles.json # 生成記事
    │   ├── note_posts.json     # note投稿記録
    │   └── x_posts.json        # X投稿記録
    ├── logs/                   # ログファイル
    ├── requirements.txt        # 依存ライブラリ
    └── README.md               # このファイル
    ```

## セットアップ方法

1.  **リポジトリのクローン**:
    ```bash
    git clone https://github.com/ni-toon/ai-affiliate-auto-poster.git
    cd ai-affiliate-auto-poster
    ```

2.  **Python環境の準備**:
    Python 3.10以上がインストールされていることを確認してください。
    仮想環境の作成を推奨します。
    ```bash
    python -m venv venv
    source venv/bin/activate  # macOS/Linux
    # venv\Scripts\activate    # Windows
    ```

3.  **依存ライブラリのインストール**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Playwrightのブラウザドライバをインストール**:
    ```bash
    playwright install
    ```

5.  **設定ファイルの作成と編集**:
    まず、テンプレートファイルをコピーして設定ファイルを作成します。
    ```bash
    cp config/config.json.template config/config.json
    ```
    
    次に、`config/config.json` ファイルを開き、以下の情報を入力します。
    *   `openai.api_key`: ご自身のOpenAI APIキー
    *   `amazon.associate_id`: AmazonアソシエイトのトラッキングID
    *   `note.username`, `note.password`: noteのログイン情報
    *   `x.username`, `x.password`: Xのログイン情報
    *   `schedule`: 投稿スケジュール（1日の投稿数、開始・終了時間など）
    *   `browser.headless`: `false`に設定すると、ブラウザの動作を目で確認しながら実行できます。

## 実行方法

### 1. テスト実行（1記事のみ）

まず、システムが正しく動作するかをテストします。以下のコマンドを実行すると、1記事の生成から投稿までが行われます。

```bash
python src/main_controller.py
```

`config.json` の `browser.headless` を `false` に設定すると、ブラウザが実際にどのように動作しているかを確認できるため、初回はこちらでの実行を推奨します。

### 2. スケジューラーによる自動実行

テストが成功したら、以下のコマンドでスケジューラーを起動します。これにより、`config.json` の設定に従って、システムがバックグラウンドで継続的に記事を自動投稿します。

```bash
python src/scheduler.py
```

このコマンドを実行したターミナルを開いたままにしておくことで、システムは稼働し続けます。停止するには `Ctrl+C` を押してください。

## 注意事項

*   **ログイン情報**: noteやXのログイン情報は、`config.json` ファイルに平文で保存されます。このファイルの取り扱いには十分ご注意ください。
*   **2段階認証**: noteやXで2段階認証を設定している場合、自動ログインに失敗する可能性があります。その場合は、一時的に2段階認証を解除するか、`headless: false` モードで実行し、手動で認証コードを入力する必要があります。
*   **利用規約**: 各プラットフォーム（note, X, Amazonアソシエイト）の利用規約を遵守してください。短期間での大量投稿はアカウントの制限につながる可能性があります。本システムの利用によって生じたいかなる問題についても、開発者は責任を負いません。
*   **エラーハンドリング**: ネットワークの問題や各サービスのUI変更により、プログラムが停止する可能性があります。定期的に `logs/` ディレクトリ内のログファイルを確認し、エラーが発生していないか監視することを推奨します。

