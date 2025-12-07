from pathlib import Path
from typing import Optional, List, Tuple
import csv

# ======= 설정값 (여기만 수정해서 사용) =======
CSV_PATH = Path(r"D:\code\exhibition\auto\personal.csv")   # csv 파일 경로
OUTPUT_DIR = Path(r"D:\code\exhibition\_portfolio")        # md 파일들이 생성될 폴더
CSV_ENCODING = "cp949"                                     # 현재 csv 인코딩 (필요시 변경)
# ============================================


def clean_output_dir(directory: Path) -> None:
    """OUTPUT_DIR 안의 기존 md 파일을 모두 삭제한다."""
    if directory.exists():
        for md_file in directory.glob("*.md"):
            try:
                md_file.unlink()
                print(f"Deleted old file: {md_file}")
            except Exception as e:
                print(f"Failed to delete {md_file}: {e}")


def normalize_web_path(path_str: str) -> str:
    """Backslash를 웹 경로용 슬래시로 바꿔준다."""
    return path_str.replace("\\", "/").strip()


def build_front_matter(title: str, name: str, grade: str, thumbnail_web_path: str) -> str:
    """
    YAML front matter 생성.
    caption.title / caption.subtitle / caption.thumbnail 채움.
    """
    caption_subtitle = f"{name}({grade})" if grade else name

    front_matter_lines = [
        "---",
        f"title: {title}",
        "subtitle: ",
        "image:",
        "alt: ",
        "",
        "caption:",
        f"  title: {title}",
        f"  subtitle: {caption_subtitle}",
        f'  thumbnail: "{thumbnail_web_path}"',
        "---",
        "",
    ]
    return "\n".join(front_matter_lines)


def build_body(
    thumbnail_path: str,
    content_cells: List[str],
    description: Optional[str] = None
) -> str:
    """
    본문(내용들 + 설명) 생성.

    - content_cells: H열 이후에 있는 모든 셀 (이미지 경로 또는 <iframe ...> 문자열)
    - description: F열 설명. 내용 블록 바로 뒤에 한 줄로 붙음.
    """
    lines: List[str] = []

    # 내용(사진/영상) 출력
    for raw in content_cells:
        cell = (raw or "").strip()
        if not cell:
            continue

        # iframe(영상)인 경우
        if cell.startswith("<iframe"):
            lines.append(cell)
        else:
            # 이미지 경로인 경우
            image_web_path = normalize_web_path(cell)
            lines.append(f"![image]({image_web_path})")

    # 만약 내용 셀이 전혀 없으면, 썸네일이라도 본문에 한 번 보여주고 싶다면:
    if not lines and thumbnail_path:
        thumb_web_path = normalize_web_path(thumbnail_path)
        lines.append(f"![image]({thumb_web_path})")

    # 설명(F열)을 내용 블록 바로 뒤에 붙이기
    if description:
        desc = description.strip()
        if desc:
            lines.append(desc)

    return "\n".join(lines) + "\n"


def row_to_markdown(row: List[str]) -> Optional[Tuple[str, str]]:
    """
    CSV 한 줄(row)을 받아:
      - 출력 파일명
      - 마크다운 전체 텍스트
    를 반환.

    컬럼 매핑:
      0: A열 - 순번
      1: B열 - 이름
      2: C열 - 학년
      3: D열 - 학번
      4: E열 - 작품 제목
      5: F열 - 설명
      6: G열 - 썸네일 경로
      7~: H열 이후 - 내용(사진 경로 or iframe 문자열)
    """
    # 최소한 G열(썸네일)까지는 있어야 한다.
    if len(row) < 7:
        return None

    index_str = row[0].strip()
    name = row[1].strip()
    grade = row[2].strip()
    title = row[4].strip()

    description = row[5].strip() if len(row) > 5 else ""
    thumb_path = row[6] if len(row) > 6 else ""

    # H열 이후 전체를 내용 리스트로 사용
    content_cells: List[str] = []
    if len(row) > 7:
        content_cells = row[7:]

    if not index_str or not name or not title:
        return None
    # 파일 이름: 01_이름_제목.md
    try:
        index_int = int(index_str)
        index_padded = f"{index_int:02d}"
    except ValueError:
        index_padded = index_str

    file_name = f"{index_padded}_{name}_{title}.md"

    # 썸네일 경로를 웹 경로 형태로
    thumb_web_path = normalize_web_path(thumb_path)

    # front matter + body 조립
    front_matter = build_front_matter(title, name, grade, thumb_web_path)
    body = build_body(thumb_path, content_cells, description)

    markdown_text = front_matter + body
    return file_name, markdown_text


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 기존 md 파일 삭제
    clean_output_dir(OUTPUT_DIR)

    with CSV_PATH.open("r", encoding=CSV_ENCODING, newline="") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            # 빈 줄 스킵
            if not row or all(not (cell or "").strip() for cell in row):
                continue

            result = row_to_markdown(row)
            if result is None:
                continue

            file_name, md_text = result
            out_path = OUTPUT_DIR / file_name

            with out_path.open("w", encoding="utf-8", newline="\n") as f:
                f.write(md_text)

            print(f"Created: {out_path}")


if __name__ == "__main__":
    main()
