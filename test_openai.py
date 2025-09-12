"""
OpenAI接続テスト用スクリプト
"""

import sys
import os
import json

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_openai_connection():
    """OpenAI接続をテスト"""
    try:
        # 設定ファイルを読み込み
        with open('config/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        api_key = config['openai']['api_key']
        print(f"APIキー: {api_key[:10]}...")
        
        # OpenAIライブラリをインポート
        import openai
        print(f"OpenAIライブラリバージョン: {openai.__version__}")
        
        # クライアントを初期化
        client = openai.OpenAI(api_key=api_key)
        print("OpenAIクライアント初期化成功")
        
        # 簡単なテスト呼び出し
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Hello, this is a test."}
            ],
            max_tokens=10
        )
        
        print("API呼び出し成功")
        print(f"レスポンス: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"エラー: {e}")
        print(f"エラータイプ: {type(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_openai_connection()

