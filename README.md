# Mini NPU: AI가 계산하는 방식을 흉내 내는 작은 계산기

**한국어** · [English](README.en.md)

3×3부터 25×25까지의 숫자 패턴을 필터와 **MAC(Multiply-Accumulate)** 연산으로 비교해 Cross와 X를 판정하는 콘솔 프로그램입니다. 저장소에는 서로 독립된 두 가지 결과물이 있습니다.

| 결과물 | 위치 | 요구 사항 |
|---|---|---|
| **A. 과제 제출 프로그램** | `main.py` | Python 3.8 이상, 표준 라이브러리만 사용 |
| **B. Rain Atlas 학습 자료** (시뮬레이터, 터미널, 런북, Manim 영상) | Docker 이미지 `jidoil/mini-npu-atlas` | Docker |

`main.py`는 웹, 노트북 도구, Manim을 import하지 않습니다. 이 저장소에는 A의 코드만 있고, B는 소스 없이 이미지로 제공합니다. 이미지를 받지 않아도 A는 그대로 동작합니다.

> **데이터 안내**: 공식 `data.json`을 받지 못해 이 저장소의 결과는 직접 만든 **데모 데이터** `fixtures/sample_data.json`으로 측정했습니다. 공식 결과가 아닙니다. 공식 파일을 저장소 맨 위에 `data.json`으로 두면 프로그램이 그 파일을 우선 사용합니다.

## 화면

공개 이미지 `jidoil/mini-npu-atlas:1.1.0`에서 찍은 화면입니다. 표시된 결과는 데모 데이터 기준입니다.

### MAC 시뮬레이터

| Day | Night |
|---|---|
| ![Day 모드의 MAC 시뮬레이터](docs/screenshots/ko/atlas-day.webp) | ![Night 모드의 MAC 시뮬레이터](docs/screenshots/ko/atlas-night.webp) |

모바일에서는 행렬과 누적 패널이 위아래로 배치됩니다.

<img src="docs/screenshots/ko/atlas-mobile.webp" alt="모바일 폭의 MAC 시뮬레이터" width="300">

### 챕터

**개념, 수식, Manim 영상.** 영상은 미리 렌더링한 것입니다.

![MAC 챕터의 개념 설명과 Manim 영상](docs/screenshots/ko/chapter-mac.webp)

**판정.** 입력을 Cross에서 X로 섞으며 점수와 결정 경계를 관찰합니다.

![α 슬라이더와 점수 차트](docs/screenshots/ko/chapter-decision.webp)

**데이터셋.** 케이스를 누르면 어느 단계에서 멈췄는지 보여 줍니다.

![케이스별 판정 표와 상세 정보](docs/screenshots/ko/chapter-dataset.webp)

**성능.** 파이썬 실측값과 N²에 대한 직선 적합입니다.

![연산 횟수에 따른 시간 차트와 측정 표](docs/screenshots/ko/chapter-performance.webp)

**최종 분석.** 실패 원인 분류와 검증 결과입니다.

![실패 분류와 검증 요약](docs/screenshots/ko/chapter-report.webp)

### 터미널

왼쪽의 실제 셸에서 과제 요구 사항을 직접 실행합니다. 오른쪽 가이드의 ▶를 누르면 명령이 셸로 전송되고, 단계별로 나와야 할 결과를 함께 보여 줍니다.

![셸과 순서별 가이드가 나란히 있는 터미널 페이지](docs/screenshots/ko/terminal.webp)

### 런북

사이트 안에서 한 셀씩 읽고, 슬라이더를 움직이면 파이썬이 다시 계산합니다.

| 처음 화면 | 슬라이더와 차트 |
|---|---|
| ![런북 처음 화면](docs/screenshots/ko/runbook.webp) | ![슬라이더로 다시 계산되는 런북 셀](docs/screenshots/ko/runbook-interactive.webp) |

## 실행 방법

### 제출 프로그램

```bash
python3 main.py                        # 모드를 메뉴에서 선택
python3 main.py --mode 1               # Mode 1: 3×3 직접 입력
python3 main.py --mode 2               # Mode 2: data.json 분석
python3 main.py --mode 2 --lang en     # 영어 출력
python3 main.py --mode 2 --data 경로.json

python3 -m unittest discover -s tests  # 단위 테스트
```

- **Mode 1**: 필터 A, 필터 B, 패턴을 한 줄씩 공백으로 구분해 입력합니다. 형식이 틀리면 안내 후 그 행렬을 다시 입력받습니다. 줄에 `cross` 또는 `x`를 입력하면 해당 배열이 자동으로 만들어집니다.
- **Mode 2**: `data.json`을 읽어 케이스별 점수, 판정, PASS/FAIL, 성능 표, 요약을 출력합니다. 파일이 없으면 "공식 데이터 아님" 경고와 함께 데모 데이터를 사용합니다.

### Rain Atlas 실행

```bash
docker compose up -d
```

처음 실행할 때 이미지를 내려받습니다(압축 크기 약 670 MiB). 이미지에는 웹, 런북, Manim, LaTeX가 모두 들어 있습니다.

| 주소 | 내용 |
|---|---|
| http://localhost:8790 | Rain Atlas (한/영, Day/Night 전환) |
| http://localhost:8790/terminal.html | 브라우저 안의 셸과 순서별 가이드 (ttyd) |
| http://localhost:8790/runbook.html | 사이트 안에 내장된 런북 (marimo) |

포트를 바꾸려면 `ATLAS_PORT=9000 docker compose up -d`를 사용합니다. 터미널과 런북은 토큰 없이 코드를 실행하므로 `127.0.0.1`에만 공개하고, nginx가 다른 사이트에서 오는 요청을 막습니다. **다른 컴퓨터에서 접근 가능하게 바꾸지 마세요.**

런북을 연 채로 서버를 재시작하면 셀이 실행되지 않은 상태로 열릴 수 있습니다. 이때는 화면의 **Restart** 버튼을 누르세요.

| 작업 | 명령 |
|---|---|
| 콘솔 프로그램 | `docker compose run --rm cli` |
| 단위 테스트 | `docker compose run --rm cli python -m unittest discover -s tests` |
| 종료 | `docker compose down` |

## 터미널

왼쪽 레일의 `00`이나 상단 `TERMINAL`을 누르면 열립니다. 환경 확인, Mode 1, Mode 2, 판정 규칙, 성능 측정, 단위 테스트까지 아홉 단계를 순서대로 실행합니다.

- 셸은 브라우저가 아니라 로컬 Docker 컨테이너에서 실행됩니다.
- 코드는 읽기 전용이고, `/tmp`에 쓴 파일은 컨테이너를 재시작하면 사라집니다.
- 페이지를 새로 고치면 셸 세션과 진행 표시가 처음으로 돌아갑니다. 언어를 바꿔도 셸 세션은 유지됩니다.

## 런북

런북은 별도 창이 아니라 **사이트 안에서** 열립니다. Atlas의 왼쪽 레일 `RB`나 상단 `RUNBOOK`을 누르면 되고, 언어와 Day/Night 전환도 Atlas와 함께 움직입니다. 수학이나 머신러닝 지식이 없어도 위에서 아래로 한 셀씩 읽으며 따라가도록 만들었습니다.

- 그림을 숫자로 바꾸는 과정부터 MAC, 내적, 신경망과의 연결, 부동소수점, 데이터셋 처리, 시간 복잡도까지 다루며 `main.py`의 실제 함수를 호출합니다.
- [marimo](https://marimo.io)를 사용합니다. 슬라이더나 체크박스를 움직이면 관련된 셀만 바로 다시 계산됩니다.
- 3×3 입력을 체크박스로 바꿔 점수와 판정을 보고, 그 입력으로 Manim 영상을 직접 렌더링할 수 있습니다.
- 파이썬은 브라우저가 아니라 로컬 Docker 컨테이너에서 실행됩니다. 컨테이너는 읽기 전용이어서, 코드를 고쳐 봐도 이미지 안의 파일은 바뀌지 않습니다.

## 구현 요약

### MAC

입력 $P$와 필터 $F$의 같은 위치 원소를 곱해 모두 더합니다. 필터를 움직이는 합성곱도, 행렬곱도 아닙니다.

```python
def mac(pattern, filter_matrix):
    n = len(pattern)
    score = 0.0
    for i in range(n):
        for j in range(n):
            score += pattern[i][j] * filter_matrix[i][j]
    return score
```

### 라벨 정규화

비교 전에 모든 라벨을 표준 라벨 `Cross`와 `X`로 바꿉니다. 앞뒤 공백과 대소문자는 무시합니다.

| 원본 | 표준 라벨 |
|---|---|
| `+`, `cross` (expected, 필터 키) | `Cross` |
| `x` (expected, 필터 키) | `X` |
| 그 밖의 값 | 추측하지 않고 해당 케이스를 FAIL로 기록 |

### Epsilon 정책

`abs(a - b) < 1e-9`이면 두 점수를 같다고 보고 `UNDECIDED`(판정 불가)를 반환합니다. Mode 2에서 `UNDECIDED`는 `expected`와 일치할 수 없으므로 FAIL입니다. 0.1 같은 소수는 2진수로 정확히 저장되지 않아 `==`로 비교하면 수학적으로 같은 합도 다르게 판정되기 때문입니다.

### 데이터 처리

키에서 N을 추출(`size_13_2` → 13)하고 `filters["size_13"]`을 찾습니다. 행과 열 수, 숫자 여부를 검사한 뒤 MAC으로 판정합니다. 한 케이스의 오류는 프로그램을 멈추지 않고 해당 케이스의 FAIL과 사유로 기록됩니다.

## 결과 리포트

측정 환경: Docker `python:3.12-slim`, Python 3.12.16, Linux aarch64, 데모 데이터 16케이스.

### 테스트 결과

- 단위 테스트 **60개 통과** (Python 3.8.20, 3.12.16, 3.14.10)
- JS와 Python 테스트 벡터 **21/21 일치**
- 데모 데이터 **전체 16, 통과 8, 실패 8**

### 실패 원인 분석

실패 8건은 모든 실패 유형이 올바르게 처리되는지 확인하려고 데모 데이터에 **일부러 넣은 것**입니다. 실패가 0건이 아닌 이유이며, `main.py`의 오류가 아닙니다.

| 케이스 | 분류 | 원인 | 고칠 곳 |
|---|---|---|---|
| `size_13_3` | NUMERICAL COMPARISON | 두 점수 차이 1.11e-16이 ε 미만이어서 UNDECIDED | 데이터 (의도된 동점) |
| `size_5_4` | MATRIX SIZE | 5행이 필요한데 4행 | 데이터 |
| `size_5_5` | LABEL NORMALIZATION | 지원하지 않는 라벨 `o` | 데이터 |
| `size_5_6` | CLASSIFICATION LOGIC | 판정 X, expected Cross | 데이터 또는 필터 |
| `size_13_4` | DATA / SCHEMA | `input` 필드 없음 | 데이터 |
| `size_25_4` | DATA / SCHEMA | (1, 1) 값이 숫자가 아닌 문자열 `'1'` | 데이터 |
| `size_7_1` | DATA / SCHEMA | 필터 그룹 `size_7` 없음 | 데이터 |
| `pattern_1` | DATA / SCHEMA | 키가 `size_N_idx` 형식이 아님 | 데이터 |

- 실패를 다섯 분류로 나누면 데이터와 코드 중 어디를 고칠지 먼저 가릴 수 있습니다.
- 스키마 오류가 4건으로 가장 많은 것은 데모 데이터의 구성 때문이며, 실제 데이터의 오류 분포를 뜻하지 않습니다.
- 라벨 오류를 표기 차이로 넘기면 틀린 데이터가 PASS가 될 수 있어, 모르는 값은 추측하지 않습니다.
- 동점을 임의로 한쪽 라벨로 처리하면 잡음이 판정을 결정하므로 UNDECIDED로 분리합니다.
- 크기가 다른 입력을 앞부분만 잘라 계산하면 틀린 점수가 조용히 나옵니다. 그래서 MAC 전에 크기를 검사합니다.
- 공식 데이터로 실행하면 실패 내용은 달라질 수 있으며, 이 표를 다시 작성해야 합니다.

### 성능 측정

웹과 아래 표는 측정 잡음을 줄이려고 크기당 2000회를 평균했습니다. 콘솔 프로그램은 과제 기준인 10회를 평균하므로 값이 더 흔들립니다. 파일 입출력과 콘솔 출력은 측정 구간에서 제외했습니다.

| 크기 | 연산 횟수 N² | 평균 시간(ms) | MAC당 시간(ns) |
|---|---:|---:|---:|
| 3×3 | 9 | 0.000578 | 64.2 |
| 5×5 | 25 | 0.001189 | 47.6 |
| 13×13 | 169 | 0.006630 | 39.2 |
| 25×25 | 625 | 0.022710 | 36.3 |

### 시간 복잡도

- `mac()`은 N×N 원소마다 곱셈과 덧셈을 한 번씩 하므로 **시간 O(N²)**, 추가 공간 O(1)입니다.
- 케이스 하나는 필터 두 개와 비교하므로 2N²번 곱하며, 차수는 그대로 O(N²)입니다.
- 실측값에 $T = a + b N^2$를 맞추면 $a = 3.55 \times 10^{-4}$ ms, $b = 3.59 \times 10^{-5}$ ms, **R² = 0.9998**로 거의 직선입니다.
- 다만 $N$에 대한 로그-로그 기울기는 이론값 2가 아니라 **1.75**입니다. 함수 호출 같은 고정 비용 $a$의 비중이 작은 크기에서 크기 때문입니다. 위 표에서 MAC당 시간이 크기가 커질수록 줄어드는 것도 같은 이유입니다.
- 예를 들어 13×13에서 25×25로 커지면 이론상 3.70배이고 실측은 3.43배입니다.
- 이론은 증가의 형태를 말하고, 실측은 그 위의 상수와 잡음까지 보여 줍니다. 값은 컴퓨터와 실행 시점에 따라 달라집니다.

### 보너스

**1차원 최적화**: 행렬을 한 줄로 펴서 곱하면 같은 O(N²)이지만 상수가 줄어듭니다. 인덱스 계산이 줄기 때문입니다. 3×3에서 0.57배, 25×25에서 0.83배 시간이 걸렸습니다(2000회 평균).

| 크기 | 2차원(ms) | 1차원(ms) | 1차원/2차원 |
|---|---:|---:|---:|
| 3×3 | 0.000584 | 0.000332 | 0.57 |
| 5×5 | 0.001242 | 0.000683 | 0.55 |
| 13×13 | 0.006156 | 0.003856 | 0.63 |
| 25×25 | 0.020888 | 0.017414 | 0.83 |

**N×N 패턴 생성기**: `make_cross(n)`, `make_x(n)`을 Mode 1 입력과 성능 측정에 함께 씁니다.

## 재현성

```bash
docker compose run --rm cli python -m unittest discover -s tests
docker compose run --rm cli python main.py --mode 2
```

- 점수, 판정, 테스트 결과는 항상 같습니다. 시간 값만 실행마다 달라집니다.
- 웹의 5~7장은 이미지를 만들 때 `main.py`의 실제 함수로 내보낸 결과를 보여 줄 뿐, 브라우저에서 Python을 실행하지 않습니다.
- 공식 데이터로 바꾸려면 `data.json`을 저장소 맨 위에 두고 `main.py`를 다시 실행합니다. 이미지 안의 Atlas와 런북은 계속 데모 데이터를 보여 줍니다.

## 구조

```text
main.py                 제출 프로그램 (표준 라이브러리만 사용)
tests/                  단위 테스트
fixtures/               데모 데이터 (공식 데이터 아님)
tools/make_fixture.py   데모 데이터 생성
docker-compose.yml      Rain Atlas 이미지 실행, 콘솔 프로그램 실행
docs/screenshots/       README 화면
```

## 한계

- 공식 `data.json`이 없어 실패 분석과 성능 값은 데모 데이터 기준입니다.
- 웹 디자인은 프로토타입 `mini_npu_rain_atlas.html`에서 출발해 정체성을 유지하면서 다듬었으므로 원본과 같지 않습니다. 원본은 실행 후 http://localhost:8790/reference/mini_npu_rain_atlas.html 에서 볼 수 있습니다.
- 웹 글꼴 일부는 Google Fonts에서 받으므로 오프라인에서는 대체 글꼴로 표시됩니다. 기능에는 영향이 없습니다.
- 터미널은 공식 릴리스 `ttyd` 1.7.7 바이너리를 빌드할 때 SHA-256으로 확인해 이미지에 넣습니다. 직접 작성한 코드가 아닙니다.
- Atlas와 런북의 소스는 이 저장소에 없으므로, 이미지 없이는 B를 실행할 수 없습니다.
- Manim 영상은 미리 렌더링한 것이며 실시간 계산이 아닙니다. 영상의 25 MAC 유닛은 설명용이며 실제 칩의 사양이 아닙니다.
