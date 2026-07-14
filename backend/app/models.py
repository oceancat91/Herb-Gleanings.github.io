from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Herb(Base):
    """中药材主表：四气、五味、归经、功效等属性。"""

    __tablename__ = "herbs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    name_zh: Mapped[str] = mapped_column(String(64), index=True)
    name_pinyin: Mapped[str | None] = mapped_column(String(128), nullable=True)
    name_en: Mapped[str | None] = mapped_column(String(128), nullable=True)
    name_latin: Mapped[str | None] = mapped_column(String(256), nullable=True)

    category: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)

    # 四气：寒/微寒/凉/平/微温/温/热/大寒
    siqi: Mapped[str | None] = mapped_column(String(16), index=True, nullable=True)
    siqi_en: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # 五味：酸咸苦甘辛等，逗号分隔
    wuwei: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    wuwei_en: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # 归经：心肝脾肺肾等，逗号分隔
    guijing: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)

    # 升降沉浮（可由功效/类别推断或留空）
    shengjiang: Mapped[str | None] = mapped_column(String(16), index=True, nullable=True)

    # 功效：顿号/逗号分隔摘要
    gongxiao: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 功效明细 JSON
    gongxiao_detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 主治
    zhuzhi: Mapped[str | None] = mapped_column(Text, nullable=True)
    zhuzhi_detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 配伍相关：禁忌配伍、十八反等
    peiwu_jinji: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 用量
    dosage_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    dosage_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    dosage_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)
    dosage_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 炮制、禁忌、安全、描述
    paozhi: Mapped[str | None] = mapped_column(Text, nullable=True)
    jinjizheng: Mapped[str | None] = mapped_column(Text, nullable=True)
    anquan: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 扩展 JSON：药理、妊娠、典籍引用等
    pharmacology: Mapped[str | None] = mapped_column(Text, nullable=True)
    classical_refs: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra: Mapped[str | None] = mapped_column(Text, nullable=True)

    wikidata_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source: Mapped[str] = mapped_column(String(128), default="本草典 Bencaodian CC BY-SA 4.0")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
