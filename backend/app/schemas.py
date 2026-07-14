from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HerbBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    name_zh: str
    name_pinyin: str | None = None
    name_latin: str | None = None
    category: str | None = None
    siqi: str | None = None
    wuwei: str | None = None
    guijing: str | None = None
    shengjiang: str | None = None
    gongxiao: str | None = None
    peiwu_jinji: str | None = None
    dosage_min: float | None = None
    dosage_max: float | None = None
    dosage_unit: str | None = None
    jinjizheng: str | None = None
    anquan: str | None = None
    zhuzhi: str | None = None


class HerbDetail(HerbBrief):
    name_en: str | None = None
    siqi_en: str | None = None
    wuwei_en: str | None = None
    gongxiao_detail: Any = None
    zhuzhi: str | None = None
    zhuzhi_detail: Any = None
    peiwu_jinji: str | None = None
    dosage_min: float | None = None
    dosage_max: float | None = None
    dosage_unit: str | None = None
    dosage_notes: str | None = None
    paozhi: Any = None
    jinjizheng: str | None = None
    anquan: str | None = None
    description: str | None = None
    pharmacology: Any = None
    classical_refs: Any = None
    extra: Any = None
    wikidata_id: str | None = None
    source: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class HerbListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[HerbBrief]


class StatsResponse(BaseModel):
    total_herbs: int
    by_siqi: dict[str, int] = Field(default_factory=dict)
    by_wuwei: dict[str, int] = Field(default_factory=dict)
    by_guijing: dict[str, int] = Field(default_factory=dict)
    by_category: dict[str, int] = Field(default_factory=dict)
    by_shengjiang: dict[str, int] = Field(default_factory=dict)


class CategoryItem(BaseModel):
    name: str
    count: int
