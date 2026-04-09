import asyncio
import os
import sys
from typing import Dict, List

import pandas as pd
from dotenv import load_dotenv
from pymilvus import MilvusClient


current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

load_dotenv(os.path.join(root_dir, ".env"))

from app.utils.ai_engine import get_embedding  # noqa: E402


COLLECTION_NAME = "anima_isle"
EXCEL_PATH = os.getenv("IMAGE_METADATA_EXCEL_PATH", os.path.join(root_dir, "data", "image_metadata.xlsx"))
IMAGE_LIBRARY_ROOT = os.getenv("IMAGE_LIBRARY_ROOT", os.path.join(root_dir, "data", "image_library"))
IMAGE_BASE_URL = os.getenv("IMAGE_BASE_URL", "").rstrip("/")
DEFAULT_POEM_CONTENT = os.getenv(
    "DEFAULT_POEM_CONTENT",
    "风吹过了海面\n你的心事被听见\n今夜请先休息",
)
DEFAULT_FALLBACK_LEVEL = int(os.getenv("DEFAULT_FALLBACK_LEVEL", "1"))

REQUIRED_COLUMNS = ["Image_ID", "Island_Target", "Visual_Prototype", "Image_Description"]
SUPPORTED_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")


def _create_client() -> MilvusClient:
    endpoint = os.getenv("ZILLIZ_ENDPOINT")
    token = os.getenv("ZILLIZ_TOKEN")
    if not endpoint or not token:
        raise ValueError("Missing Zilliz configuration in .env")
    return MilvusClient(uri=endpoint, token=token)


def _normalize_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _compose_semantic_text(row: Dict[str, str]) -> str:
    visual = row["Visual_Prototype"]
    description = row["Image_Description"]
    if visual and description:
        return f"{visual}。{description}"
    return visual or description


def _sheet_intensity(sheet_name: str) -> str:
    parts = sheet_name.split("_")
    return parts[-1] if len(parts) >= 2 else ""


def _resolve_image_path(sheet_name: str, image_id: str) -> str:
    for extension in SUPPORTED_IMAGE_EXTENSIONS:
        candidate = os.path.join(IMAGE_LIBRARY_ROOT, sheet_name, f"{image_id}{extension}")
        if os.path.exists(candidate):
            return candidate
    raise FileNotFoundError(f"找不到图片文件: sheet={sheet_name}, image_id={image_id}")


def _build_image_url(sheet_name: str, image_id: str, image_path: str) -> str:
    if IMAGE_BASE_URL:
        extension = os.path.splitext(image_path)[1]
        return f"{IMAGE_BASE_URL}/{sheet_name}/{image_id}{extension}"
    return image_path


def _read_excel_rows() -> List[Dict[str, str]]:
    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError(f"找不到 Excel 文件: {EXCEL_PATH}")

    workbook = pd.read_excel(EXCEL_PATH, sheet_name=None).items()
    rows: List[Dict[str, str]] = []

    for sheet_name, dataframe in workbook:
        if dataframe.empty:
            continue

        normalized_columns = {column: str(column).strip() for column in dataframe.columns}
        dataframe = dataframe.rename(columns=normalized_columns).fillna("")

        missing_columns = [column for column in REQUIRED_COLUMNS if column not in dataframe.columns]
        if missing_columns:
            raise ValueError(f"Sheet {sheet_name} 缺少列: {', '.join(missing_columns)}")

        for _, raw_row in dataframe.iterrows():
            image_id = _normalize_text(raw_row.get("Image_ID"))
            island_target = _normalize_text(raw_row.get("Island_Target"))
            visual_prototype = _normalize_text(raw_row.get("Visual_Prototype"))
            image_description = _normalize_text(raw_row.get("Image_Description"))
            poem_content = _normalize_text(raw_row.get("poem_content") or raw_row.get("Poem_Content")) or DEFAULT_POEM_CONTENT
            fallback_level = _normalize_text(raw_row.get("Fallback_level")) or str(DEFAULT_FALLBACK_LEVEL)

            if not image_id or not island_target:
                continue

            rows.append(
                {
                    "sheet_name": sheet_name,
                    "Image_ID": image_id,
                    "Island_Target": island_target,
                    "Visual_Prototype": visual_prototype,
                    "Image_Description": image_description,
                    "poem_content": poem_content,
                    "Fallback_level": fallback_level,
                }
            )

    return rows


def ingest_data() -> None:
    rows = _read_excel_rows()
    if not rows:
        print("没有可导入的数据。")
        return

    client = _create_client()
    payloads = []

    print(f"开始处理 {len(rows)} 条素材记录...")

    for index, row in enumerate(rows, start=1):
        semantic_text = _compose_semantic_text(row)
        if not semantic_text:
            print(f"跳过第 {index} 条：缺少可生成 embedding 的文本")
            continue

        try:
            image_path = _resolve_image_path(row["sheet_name"], row["Image_ID"])
        except FileNotFoundError as error:
            print(str(error))
            continue

        vector = asyncio.run(get_embedding(semantic_text))
        if vector is None:
            print(f"跳过第 {index} 条：embedding 生成失败")
            continue

        payloads.append(
            {
                "id": row["Image_ID"],
                "vector": vector,
                "Image_ID": row["Image_ID"],
                "Island_Target": row["Island_Target"],
                "Sheet_Name": row["sheet_name"],
                "Emotion_Intensity": _sheet_intensity(row["sheet_name"]),
                "Visual_Prototype": row["Visual_Prototype"],
                "Image_Description": row["Image_Description"],
                "Semantic_text": semantic_text,
                "poem_content": row["poem_content"],
                "image_url": _build_image_url(row["sheet_name"], row["Image_ID"], image_path),
                "Fallback_level": int(row["Fallback_level"]),
            }
        )
        print(f"已处理 {index}/{len(rows)}: {row['Image_ID']}")

    if not payloads:
        print("没有有效数据被写入。")
        return

    print(f"准备写入 {len(payloads)} 条数据到 {COLLECTION_NAME}...")
    result = client.insert(collection_name=COLLECTION_NAME, data=payloads)
    print(f"写入完成: {result}")


if __name__ == "__main__":
    ingest_data()
