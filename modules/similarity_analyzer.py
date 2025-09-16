#!/usr/bin/env python3
"""
高度な類似度分析モジュール
複数のアルゴリズムを組み合わせて記事の類似度を判定する
"""

import re
import math
from typing import Dict, List, Tuple, Set
from collections import Counter
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)

class SimilarityAnalyzer:
    def __init__(self):
        # 日本語のストップワード（除外する一般的な単語）
        self.stop_words = {
            'の', 'に', 'は', 'を', 'が', 'で', 'と', 'から', 'まで', 'より', 'も',
            'こと', 'もの', 'ため', 'など', 'について', 'により', 'による', 'として',
            'です', 'である', 'ます', 'だ', 'である', 'ある', 'いる', 'する', 'なる',
            'この', 'その', 'あの', 'どの', 'これ', 'それ', 'あれ', 'どれ',
            'ここ', 'そこ', 'あそこ', 'どこ', '今', '昨日', '明日', '今日',
            '記事', '本記事', '今回', '以下', '上記', '下記', '参考', '詳細'
        }
        
        # 重要なキーワードの重み
        self.keyword_weights = {
            'おすすめ': 2.0,
            'レビュー': 2.0,
            '効果': 1.8,
            'メリット': 1.5,
            'デメリット': 1.5,
            '使い方': 1.8,
            '方法': 1.5,
            '比較': 1.8,
            '評価': 1.5,
            '価格': 1.3,
            '機能': 1.3,
            '特徴': 1.3
        }
    
    def analyze_similarity(self, content1: str, content2: str) -> Dict[str, float]:
        """
        複数のアルゴリズムを使用して包括的な類似度分析を実行
        
        Args:
            content1: 記事内容1
            content2: 記事内容2
        
        Returns:
            Dict[str, float]: 各種類似度スコア
        """
        try:
            # 内容を正規化
            normalized1 = self.normalize_content(content1)
            normalized2 = self.normalize_content(content2)
            
            # 各種類似度を計算
            results = {
                'sequence_similarity': self.calculate_sequence_similarity(normalized1, normalized2),
                'cosine_similarity': self.calculate_cosine_similarity(normalized1, normalized2),
                'jaccard_similarity': self.calculate_jaccard_similarity(normalized1, normalized2),
                'keyword_similarity': self.calculate_keyword_similarity(content1, content2),
                'structure_similarity': self.calculate_structure_similarity(content1, content2)
            }
            
            # 総合類似度を計算（重み付き平均）
            weights = {
                'sequence_similarity': 0.25,
                'cosine_similarity': 0.25,
                'jaccard_similarity': 0.20,
                'keyword_similarity': 0.20,
                'structure_similarity': 0.10
            }
            
            overall_similarity = sum(
                results[key] * weights[key] 
                for key in weights.keys()
            )
            
            results['overall_similarity'] = overall_similarity
            
            return results
            
        except Exception as e:
            logger.error(f"類似度分析でエラー: {e}")
            return {
                'sequence_similarity': 0.0,
                'cosine_similarity': 0.0,
                'jaccard_similarity': 0.0,
                'keyword_similarity': 0.0,
                'structure_similarity': 0.0,
                'overall_similarity': 0.0
            }
    
    def normalize_content(self, content: str) -> str:
        """記事内容を正規化"""
        # URLを除去
        content = re.sub(r'https?://[^\s]+', '', content)
        
        # 免責事項を除去
        content = re.sub(r'※本記事にはアフィリエイトリンクを含みます', '', content)
        
        # Markdownの見出し記号を除去
        content = re.sub(r'#+\s*', '', content)
        
        # 改行と空白を正規化
        content = re.sub(r'\s+', ' ', content)
        
        # 記号を除去（ただし、重要な区切り文字は保持）
        content = re.sub(r'[^\w\s。、！？]', '', content)
        
        return content.strip()
    
    def calculate_sequence_similarity(self, content1: str, content2: str) -> float:
        """シーケンス類似度を計算（SequenceMatcher使用）"""
        try:
            return SequenceMatcher(None, content1, content2).ratio()
        except Exception as e:
            logger.error(f"シーケンス類似度計算エラー: {e}")
            return 0.0
    
    def calculate_cosine_similarity(self, content1: str, content2: str) -> float:
        """コサイン類似度を計算"""
        try:
            # 単語ベクトルを作成
            words1 = self.extract_words(content1)
            words2 = self.extract_words(content2)
            
            # 単語の出現回数をカウント
            counter1 = Counter(words1)
            counter2 = Counter(words2)
            
            # 全ての単語の集合を取得
            all_words = set(counter1.keys()) | set(counter2.keys())
            
            if not all_words:
                return 0.0
            
            # ベクトルを作成
            vector1 = [counter1.get(word, 0) for word in all_words]
            vector2 = [counter2.get(word, 0) for word in all_words]
            
            # コサイン類似度を計算
            dot_product = sum(a * b for a, b in zip(vector1, vector2))
            magnitude1 = math.sqrt(sum(a * a for a in vector1))
            magnitude2 = math.sqrt(sum(a * a for a in vector2))
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            return dot_product / (magnitude1 * magnitude2)
            
        except Exception as e:
            logger.error(f"コサイン類似度計算エラー: {e}")
            return 0.0
    
    def calculate_jaccard_similarity(self, content1: str, content2: str) -> float:
        """Jaccard類似度を計算"""
        try:
            words1 = set(self.extract_words(content1))
            words2 = set(self.extract_words(content2))
            
            if not words1 and not words2:
                return 1.0
            
            intersection = words1 & words2
            union = words1 | words2
            
            if not union:
                return 0.0
            
            return len(intersection) / len(union)
            
        except Exception as e:
            logger.error(f"Jaccard類似度計算エラー: {e}")
            return 0.0
    
    def calculate_keyword_similarity(self, content1: str, content2: str) -> float:
        """重要キーワードに基づく類似度を計算"""
        try:
            keywords1 = self.extract_weighted_keywords(content1)
            keywords2 = self.extract_weighted_keywords(content2)
            
            if not keywords1 and not keywords2:
                return 0.0
            
            # 共通キーワードの重みを計算
            common_weight = 0.0
            total_weight1 = sum(keywords1.values())
            total_weight2 = sum(keywords2.values())
            
            for keyword in keywords1:
                if keyword in keywords2:
                    common_weight += min(keywords1[keyword], keywords2[keyword])
            
            if total_weight1 == 0 and total_weight2 == 0:
                return 0.0
            
            # 正規化された類似度を計算
            max_total_weight = max(total_weight1, total_weight2)
            if max_total_weight == 0:
                return 0.0
            
            return common_weight / max_total_weight
            
        except Exception as e:
            logger.error(f"キーワード類似度計算エラー: {e}")
            return 0.0
    
    def calculate_structure_similarity(self, content1: str, content2: str) -> float:
        """記事構造の類似度を計算"""
        try:
            structure1 = self.extract_structure(content1)
            structure2 = self.extract_structure(content2)
            
            # 見出しの類似度
            headings1 = set(structure1['headings'])
            headings2 = set(structure2['headings'])
            
            if not headings1 and not headings2:
                heading_similarity = 1.0
            elif not headings1 or not headings2:
                heading_similarity = 0.0
            else:
                common_headings = headings1 & headings2
                all_headings = headings1 | headings2
                heading_similarity = len(common_headings) / len(all_headings)
            
            # 段落数の類似度
            para_count1 = structure1['paragraph_count']
            para_count2 = structure2['paragraph_count']
            
            if para_count1 == 0 and para_count2 == 0:
                paragraph_similarity = 1.0
            else:
                max_para = max(para_count1, para_count2)
                min_para = min(para_count1, para_count2)
                paragraph_similarity = min_para / max_para if max_para > 0 else 0.0
            
            # 構造類似度の重み付き平均
            return (heading_similarity * 0.7) + (paragraph_similarity * 0.3)
            
        except Exception as e:
            logger.error(f"構造類似度計算エラー: {e}")
            return 0.0
    
    def extract_words(self, content: str) -> List[str]:
        """内容から単語を抽出（ストップワード除去）"""
        # 簡易的な単語分割（実際の実装では形態素解析を推奨）
        words = re.findall(r'\w+', content.lower())
        
        # ストップワードを除去
        filtered_words = [word for word in words if word not in self.stop_words and len(word) > 1]
        
        return filtered_words
    
    def extract_weighted_keywords(self, content: str) -> Dict[str, float]:
        """重み付きキーワードを抽出"""
        keywords = {}
        
        for keyword, weight in self.keyword_weights.items():
            count = content.lower().count(keyword)
            if count > 0:
                keywords[keyword] = count * weight
        
        return keywords
    
    def extract_structure(self, content: str) -> Dict:
        """記事構造を抽出"""
        # 見出しを抽出
        headings = re.findall(r'#+\s*(.+)', content)
        headings = [heading.strip().lower() for heading in headings]
        
        # 段落数をカウント
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)
        
        return {
            'headings': headings,
            'paragraph_count': paragraph_count
        }
    
    def is_similar(self, similarity_scores: Dict[str, float], threshold: float = 0.7) -> Tuple[bool, str]:
        """
        類似度スコアに基づいて類似判定を行う
        
        Args:
            similarity_scores: 類似度スコア辞書
            threshold: 類似判定の閾値
        
        Returns:
            Tuple[bool, str]: (類似しているか, 判定理由)
        """
        overall_similarity = similarity_scores.get('overall_similarity', 0.0)
        
        if overall_similarity >= threshold:
            # 詳細な判定理由を生成
            high_scores = []
            for key, score in similarity_scores.items():
                if key != 'overall_similarity' and score >= 0.6:
                    high_scores.append(f"{key}: {score:.2f}")
            
            reason = f"総合類似度 {overall_similarity:.2f} (閾値: {threshold})"
            if high_scores:
                reason += f", 高スコア項目: {', '.join(high_scores)}"
            
            return True, reason
        
        return False, f"総合類似度 {overall_similarity:.2f} < 閾値 {threshold}"

# 使用例とテスト
if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(level=logging.INFO)
    
    # 類似度分析器のインスタンス作成
    analyzer = SimilarityAnalyzer()
    
    # テスト用記事
    article1 = """
    ## フィットネスバイクのメリット
    
    フィットネスバイクは自宅で手軽にできる有酸素運動です。
    静音設計なので、早朝や深夜でも周囲を気にせず運動できます。
    継続することで健康的にダイエットができます。
    
    ## 使い方のポイント
    
    正しい姿勢で漕ぐことが重要です。
    負荷を調整しながら無理のない範囲で行いましょう。
    """
    
    article2 = """
    ## エアロバイクの効果
    
    エアロバイクは家庭で簡単にできる運動器具です。
    音が静かなので、時間を気にせずトレーニングできます。
    定期的に使用することで効果的なダイエットが可能です。
    
    ## 効果的な使用方法
    
    適切なフォームで運動することが大切です。
    強度を段階的に上げながら継続しましょう。
    """
    
    article3 = """
    ## タロットカードの基本
    
    タロット占いは古くから親しまれている占術です。
    78枚のカードを使って未来を占います。
    初心者でも簡単に始めることができます。
    
    ## 占い方の手順
    
    カードをシャッフルして質問を思い浮かべます。
    直感に従ってカードを選びましょう。
    """
    
    print("=== 類似度分析テスト ===")
    
    # 類似記事の比較
    print("\n1. 類似記事の比較（フィットネスバイク vs エアロバイク）")
    scores1 = analyzer.analyze_similarity(article1, article2)
    is_similar1, reason1 = analyzer.is_similar(scores1, threshold=0.6)
    
    print(f"類似判定: {is_similar1}")
    print(f"判定理由: {reason1}")
    print("詳細スコア:")
    for key, score in scores1.items():
        print(f"  {key}: {score:.3f}")
    
    # 非類似記事の比較
    print("\n2. 非類似記事の比較（フィットネスバイク vs タロット）")
    scores2 = analyzer.analyze_similarity(article1, article3)
    is_similar2, reason2 = analyzer.is_similar(scores2, threshold=0.6)
    
    print(f"類似判定: {is_similar2}")
    print(f"判定理由: {reason2}")
    print("詳細スコア:")
    for key, score in scores2.items():
        print(f"  {key}: {score:.3f}")

