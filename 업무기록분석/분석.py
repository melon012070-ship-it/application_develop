import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

CSV_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "업무기록_샘플.csv"


def load_data(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df["날짜"] = pd.to_datetime(df["날짜"])
    return df


def print_summary(df: pd.DataFrame) -> None:
    by_task = df.groupby("업무종류").agg(
        총소요시간=("소요시간(분)", "sum"),
        평균소요시간=("소요시간(분)", "mean"),
        총반복횟수=("반복횟수", "sum"),
        건당평균시간=("소요시간(분)", lambda s: (s / df.loc[s.index, "반복횟수"]).mean()),
    ).round(1).sort_values("총소요시간", ascending=False)

    print("=== 업무별 요약 ===")
    print(by_task.to_string())
    print()

    print("=== 자주 언급된 애매했던 점 (상위 5개) ===")
    pain_points = df["애매했던점"].dropna()
    pain_points = pain_points[pain_points.str.strip() != ""]
    print(pain_points.value_counts().head(5).to_string())
    print()

    top_task = by_task.index[0]
    print(f"가장 많은 시간을 잡아먹는 업무: {top_task} (총 {by_task.loc[top_task, '총소요시간']}분)")


def plot_summary(df: pd.DataFrame, out_path: Path) -> None:
    by_task = df.groupby("업무종류")["소요시간(분)"].sum().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(6, 4))
    by_task.plot(kind="bar", ax=ax, color="#4C72B0")
    ax.set_ylabel("총 소요시간(분)")
    ax.set_title("업무별 누적 소요시간")
    ax.tick_params(axis="x", rotation=0)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    print(f"\n그래프 저장됨: {out_path}")


def main() -> None:
    df = load_data(CSV_PATH)
    print_summary(df)
    plot_summary(df, CSV_PATH.parent / "업무별_소요시간.png")


if __name__ == "__main__":
    main()
