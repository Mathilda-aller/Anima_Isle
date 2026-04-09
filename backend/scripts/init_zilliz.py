import os
import sys

from dotenv import load_dotenv
from pymilvus import DataType, MilvusClient


current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

load_dotenv(os.path.join(root_dir, ".env"))

COLLECTION_NAME = "anima_isle"


def _create_client() -> MilvusClient:
    endpoint = os.getenv("ZILLIZ_ENDPOINT")
    token = os.getenv("ZILLIZ_TOKEN")
    if not endpoint or not token:
        raise ValueError("Missing Zilliz configuration in .env")
    return MilvusClient(uri=endpoint, token=token)


def create_database() -> None:
    client = _create_client()

    if client.has_collection(collection_name=COLLECTION_NAME):
        print(f"检测到旧集合 {COLLECTION_NAME}，正在删除...")
        client.drop_collection(collection_name=COLLECTION_NAME)
        print("删除成功。")

    schema = MilvusClient.create_schema(
        auto_id=False,
        enable_dynamic_field=True,
        description="言屿图片素材向量库",
    )

    schema.add_field(field_name="id", datatype=DataType.VARCHAR, max_length=128, is_primary=True)
    schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=1024)
    schema.add_field(field_name="Image_ID", datatype=DataType.VARCHAR, max_length=128)
    schema.add_field(field_name="Island_Target", datatype=DataType.VARCHAR, max_length=64)
    schema.add_field(field_name="Sheet_Name", datatype=DataType.VARCHAR, max_length=64)
    schema.add_field(field_name="Emotion_Intensity", datatype=DataType.VARCHAR, max_length=32)
    schema.add_field(field_name="Visual_Prototype", datatype=DataType.VARCHAR, max_length=4096)
    schema.add_field(field_name="Image_Description", datatype=DataType.VARCHAR, max_length=2048)
    schema.add_field(field_name="Semantic_text", datatype=DataType.VARCHAR, max_length=4096)
    schema.add_field(field_name="poem_content", datatype=DataType.VARCHAR, max_length=1024)
    schema.add_field(field_name="image_url", datatype=DataType.VARCHAR, max_length=2048)
    schema.add_field(field_name="Fallback_level", datatype=DataType.INT64)

    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="vector",
        index_type="AUTOINDEX",
        metric_type="COSINE",
    )

    print(f"正在创建集合 {COLLECTION_NAME}...")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        schema=schema,
        index_params=index_params,
    )
    print(f"集合 {COLLECTION_NAME} 创建成功。")
    print(client.describe_collection(collection_name=COLLECTION_NAME))


if __name__ == "__main__":
    create_database()
