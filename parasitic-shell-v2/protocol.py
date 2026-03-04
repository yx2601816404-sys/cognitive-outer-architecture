"""
protocol.py — 三体通信协议数据结构
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import Optional


class RiskLevel(IntEnum):
    """风险等级"""
    TRIVIAL = 0      # 闲聊、简单查询 → 只走 Judge
    LOW = 1          # 信息检索、格式转换 → Judge 快速通路
    MEDIUM = 2       # 需要推理但不涉及决策 → Judge + Thinker
    HIGH = 3         # 涉及决策、建议 → Judge + Thinker + Nerve
    CRITICAL = 4     # 涉及财务、关系、健康 → 三体全开 + 人工确认
    FORBIDDEN = 5    # 触犯底线 → 直接拒绝


@dataclass
class Request:
    """请求结构"""
    user_message: str
    system_message: Optional[str] = None
    messages: list[dict] = None
    risk_level: Optional[RiskLevel] = None
    route: Optional[str] = None  # "judge" | "judge+thinker" | "full"
    
    def __post_init__(self):
        if self.messages is None:
            self.messages = []


@dataclass
class SubconsciousQuery:
    """潜意识下潜请求"""
    query: str
    reason: str
    
    def to_xml(self) -> str:
        """转换为 XML 标签"""
        return f"""<SUBCONSCIOUS_QUERY>
  <query>{self.query}</query>
  <reason>{self.reason}</reason>
</SUBCONSCIOUS_QUERY>"""


@dataclass
class Pain:
    """痛觉结构"""
    type: str  # "api_error" | "user_dissatisfaction" | "value_violation"
    severity: int  # 1-5
    context: str
    raw_signal: str
    timestamp: str
    
    def to_json(self) -> dict:
        """转换为 JSON"""
        return {
            "type": self.type,
            "severity": self.severity,
            "context": self.context,
            "raw_signal": self.raw_signal,
            "timestamp": self.timestamp,
        }
    
    def to_prompt_text(self) -> str:
        """转换为 prompt 文本"""
        severity_desc = ["", "轻微", "一般", "严重", "非常严重", "致命"][self.severity]
        return f"""[PAIN_FEEDBACK] {severity_desc}痛觉
类型: {self.type}
上下文: {self.context}
原始信号: {self.raw_signal}
时间: {self.timestamp}

这是上次输出导致的痛觉反馈。请在本次推理中避免重复同样的错误。"""


@dataclass
class ArchiveFragment:
    """档案片段"""
    content: str
    source: str  # "chassis" | "history"
    relevance_score: float
    
    def to_prompt_text(self) -> str:
        """转换为 prompt 文本"""
        return f"""[ARCHIVE_FRAGMENT] 来源: {self.source}
相关度: {self.relevance_score:.2f}

{self.content}"""


@dataclass
class RouteDecision:
    """路由决策"""
    risk_level: RiskLevel
    route: str  # "judge" | "judge+thinker" | "full"
    reason: str
    estimated_cost: float  # 相对成本（1x, 2x, 3x）
    estimated_latency: float  # 相对延迟（1x, 1.5x, 2x, 3x）
