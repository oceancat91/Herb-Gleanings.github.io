"""下载本草典开源药材数据（CC BY-SA 4.0）。"""

from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "herbs_raw.json"
URL = "https://bencaodian.org/data/v1/herbs.json"


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    print(f"下载中：{URL}")
    req = Request(URL, headers={"User-Agent": "BencaoShizhen-CourseProject/1.0"})
    with urlopen(req, timeout=60) as resp:
        data = resp.read()
    OUT.write_bytes(data)
    print(f"已保存：{OUT}（{len(data)} bytes）")
    print("许可：CC BY-SA 4.0 · 署名：Bencaodian Editorial / 本草典编辑部")


if __name__ == "__main__":
    main()
