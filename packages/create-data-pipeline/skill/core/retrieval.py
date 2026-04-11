"""
统一检索引擎 - BM25 + 中文分词混合检索

取代原有的简单词频关键词匹配，为 ingest/query/lint/graph 提供统一的相关性检索。
支持中英文混合分词，TF-IDF 加权，BM25 评分。
"""

import re
import math
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import Counter

# ---- 分词 ----
# 中文停用词（高频无意义词）
_CN_STOPWORDS = set(
    "的了和是在有这那我你他她它们与或但而也都就很太最更还再又才已"
    "已经正在将要会能可以应该必须需要这个那个这些那些什么怎么为什么哪里"
    "因为所以如果虽然但是而且或者还是之一方面部分整体全部一些一点"
    "进行实施开展推进落实执行完成实现新最新最近现在今天明天昨天时候时间"
    "推出发布宣布表示说认为指出说明解释就是从到等"
)

_EN_STOPWORDS = set(
    "the a an and or but in on at for with is are was were be been being to of by "
    "from up down over under again further then once here there when where why how "
    "all any both each few more most other some such no nor not only own same so "
    "than too very do does did has have had its this that these those".split()
)


def tokenize(text: str) -> List[str]:
    """中英文混合分词：英文按词边界，中文按 bigram 切分。"""
    tokens = []
    text_lower = text.lower()

    # 英文单词（长度>=2）
    en_words = re.findall(r'\b[a-z][a-z0-9\-]{1,30}\b', text_lower)
    for w in en_words:
        if w not in _EN_STOPWORDS:
            tokens.append(w)

    # 中文序列 → bigram 分词（无需依赖jieba等外部库）
    cn_seqs = re.findall(r'[\u4e00-\u9fff]+', text_lower)
    for seq in cn_seqs:
        # 保留完整 2~6 字词
        if 2 <= len(seq) <= 6 and seq not in _CN_STOPWORDS:
            tokens.append(seq)
        # bigram
        if len(seq) >= 2:
            for i in range(len(seq) - 1):
                bg = seq[i:i + 2]
                if bg not in _CN_STOPWORDS:
                    tokens.append(bg)

    # 英文+数字组合（如 MaxQ, RAG, GPT-4）
    mixed = re.findall(r'[a-zA-Z][a-zA-Z0-9\-]*\d+[a-zA-Z0-9]*|[A-Z]{2,}', text)
    for m in mixed:
        tokens.append(m.lower())

    return tokens


# ---- BM25 ----

class BM25Index:
    """
    BM25 检索索引 (Okapi BM25)

    参数: k1=1.5, b=0.75

    用法:
        index = BM25Index()
        index.add("doc1", "这是文档1的内容...")
        index.add("doc2", "这是文档2的内容...")
        results = index.search("查询关键词", top_k=5)
        # results: [("doc1", 3.2), ("doc2", 1.1)]
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

        self.doc_tokens: Dict[str, List[str]] = {}  # doc_id → tokens
        self.doc_len: Dict[str, int] = {}            # doc_id → token count
        self.avgdl: float = 0.0                      # 平均文档长度

        # 逆文档频率
        self._df: Counter = Counter()  # term → 包含该 term 的文档数
        self._n: int = 0               # 总文档数

        self._dirty = True

    def add(self, doc_id: str, content: str):
        """添加文档到索引"""
        tokens = tokenize(content)
        self.doc_tokens[doc_id] = tokens
        self.doc_len[doc_id] = len(tokens)
        unique_terms = set(tokens)
        for t in unique_terms:
            self._df[t] += 1
        self._n += 1
        self._dirty = True

    def _recompute(self):
        if not self._dirty:
            return
        total = sum(self.doc_len.values())
        self.avgdl = total / max(self._n, 1)
        self._dirty = False

    def _idf(self, term: str) -> float:
        df = self._df.get(term, 0)
        return math.log((self._n - df + 0.5) / (df + 0.5) + 1.0)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        搜索与 query 最相关的文档

        Returns:
            [(doc_id, score), ...] 按分数降序排列
        """
        self._recompute()
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores: Dict[str, float] = {}

        for doc_id, doc_toks in self.doc_tokens.items():
            tf_counter = Counter(doc_toks)
            dl = self.doc_len[doc_id]
            score = 0.0

            for qt in query_tokens:
                tf = tf_counter.get(qt, 0)
                if tf == 0:
                    continue
                idf = self._idf(qt)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * dl / max(self.avgdl, 1))
                score += idf * numerator / denominator

            if score > 0:
                scores[doc_id] = score

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

    def search_with_content(
        self, query: str, top_k: int = 10
    ) -> List[Tuple[str, float, str]]:
        """搜索并返回 (doc_id, score, first_200_chars)"""
        results = self.search(query, top_k)
        out = []
        for doc_id, score in results:
            tokens_preview = " ".join(self.doc_tokens.get(doc_id, [])[:50])
            out.append((doc_id, score, tokens_preview[:200]))
        return out


def build_wiki_index(wiki_dir: Path) -> BM25Index:
    """从 wiki 目录构建 BM25 索引"""
    index = BM25Index()
    for p in wiki_dir.rglob("*.md"):
        if p.name in ("index.md", "log.md", "lint-report.md"):
            continue
        try:
            content = p.read_text(encoding="utf-8")
            doc_id = str(p.relative_to(wiki_dir))
            index.add(doc_id, content)
        except Exception:
            pass
    return index
