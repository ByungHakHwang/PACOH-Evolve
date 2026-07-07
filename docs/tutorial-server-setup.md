# OpenEvolve Tutorial Server Setup

이 문서는 OpenEvolve 튜토리얼에서 참가자들이 로컬 설치 없이 브라우저로
circle packing 진화 과정을 보고, 각자 서버 위에서 OpenEvolve run을 실행할 수
있도록 준비하는 절차를 정리한 runbook이다.

민감정보는 이 문서에 기록하지 않는다. 서버 접속 비밀번호, API key, 개인 계정
정보는 별도 안전한 채널로 관리한다.

## 운영 가정

튜토리얼은 발표 40분 뒤에 이어지는 40분 hands-on 세션으로 진행한다.
참가자는 약 20명이며, 목표는 참가자 전원이 서버 dashboard에 접속해서 자기
OpenEvolve job을 한 번 제출해보고, queue에서 running으로 넘어가며 checkpoint가
갱신되는 과정을 관찰하는 것이다.

40분 안에 모든 참가자의 긴 live evolution이 끝나는 것을 목표로 삼지 않는다.
대신 live run은 queue로 계속 처리되게 만들고, score function 비교와 좋은/나쁜
결과 해석은 미리 계산해 둔 replay run을 기본 설명 자료로 사용한다.

## 목표

튜토리얼에서 원하는 사용자 경험은 다음과 같다.

1. 참가자는 노트북에 OpenEvolve, scipy, streamlit 등을 설치하지 않는다.
2. 참가자는 브라우저로 서버 dashboard에 접속한다.
3. 참가자는 이름 또는 job id를 입력하고 `Start`를 누른다.
4. 서버가 참가자별 OpenEvolve job을 실행한다.
5. dashboard는 stable checkpoint의 best circle packing, score 변화, 로그를
   실시간에 가깝게 보여준다.
6. 서버 과부하가 생기면 job을 버리지 않고 queue에 넣어 느리더라도 처리한다.
7. 발표자는 precomputed replay run으로 score function 차이를 안정적으로 설명한다.

핵심 메시지는 "LLM이 후보 코드를 만들고, evaluator가 유효성을 검증하며, best
packing이 점진적으로 바뀐다"는 것을 참가자가 자기 run으로 확인하게 하는 것이다.

## 전체 구조

```text
participant browser
        |
        v
server dashboard, e.g. Streamlit
        |
        +-- creates one run directory per participant
        +-- launches OpenEvolve subprocesses
        +-- watches logs and checkpoint best_program.py files
        +-- executes checkpoint best_program.py safely enough for visualization
        +-- renders circle packing, score plot, and log tail
        |
        v
server OpenEvolve
        |
        +-- server evaluator
        +-- server scipy/numpy
        |
        v
server Ollama at http://localhost:11434/v1
        |
        v
gpt-oss:20b
```

참가자 노트북에서는 브라우저만 필요하다. OpenEvolve 실행, evaluator 실행,
visualization용 best program 실행, Ollama 호출은 모두 서버에서 일어난다.

이 저장소에는 위 구조의 실제 fallback dashboard가 `tutorial/server/`에 들어 있다.
설치와 실행 절차는 [tutorial/server/README.md](../tutorial/server/README.md)를
기준으로 한다. 운영 개요는 [tutorial-live-dashboard.md](tutorial-live-dashboard.md)에
따로 정리했다.

## 현재 서버에서 확인한 상태

실험 중 확인한 서버 상태는 다음과 같다.

```text
host: turing
OpenEvolve command: /usr/local/bin/openevolve-run
actual OpenEvolve command: /opt/openevolve/bin/openevolve-run
OpenEvolve Python: /opt/openevolve/bin/python
OpenEvolve version: 0.2.27
local repo OpenEvolve version checked during review: 0.3.0
Ollama endpoint: http://localhost:11434/v1
Ollama models:
  - gpt-oss:20b
  - gpt-oss:latest
```

서버의 OpenEvolve는 0.2.27이고 로컬 클론은 0.3.0이다. 현재 문서에서 쓰는
config 구조와 output directory 구조는 호환되는 것으로 확인했지만, 구현 중에는
서버 버전을 기준으로 smoke test를 다시 실행한다.

`/opt/openevolve` 환경에는 `scipy`가 없었다. 실험에서는 다음 위치에 사용자별
Python dependency를 설치하고 `PYTHONPATH`로 붙였다.

```text
~/openevolve_pydeps
```

이 방식은 `/opt/openevolve`를 root 권한 없이 수정하지 않아도 되므로 튜토리얼
운영에 적합하다.

## 서버 디렉터리 배치

권장 디렉터리 구조:

```text
~/openevolve_tutorial/
  circle_packing/
    initial_program.py
    evaluator.py
    config_tutorial.yaml
    README.md

~/openevolve_tutorial_runs/
  <participant_id>/
    <timestamp>/
      logs/
      checkpoints/
      best/

~/openevolve_tutorial_replays/
  hard_valid_sum/
  soft_penalty/
  intentionally_bad_reported_sum/

~/openevolve_pydeps/
  numpy/
  scipy/
  ...

~/openevolve_dashboard/
  app.py
  job_manager.py
  visualize.py
  requirements.txt
```

`openevolve_tutorial`은 read-only template처럼 취급하고, 참가자별 산출물은
반드시 `openevolve_tutorial_runs` 아래에 분리한다.

## 1. Dependency 준비

OpenEvolve 자체는 `/opt/openevolve`를 사용한다. 추가 패키지는 사용자 홈에 설치한다.

```bash
mkdir -p ~/openevolve_pydeps
/opt/openevolve/bin/python -m pip install --target "$HOME/openevolve_pydeps" scipy numpy
```

dashboard용 패키지는 별도 venv를 권장한다.

```bash
python3 -m venv ~/tutorial-dashboard-venv
source ~/tutorial-dashboard-venv/bin/activate
pip install streamlit pandas matplotlib plotly pyyaml
```

OpenEvolve subprocess를 실행할 때는 `PYTHONPATH`를 설정한다.

```bash
PYTHONPATH="$HOME/openevolve_pydeps" /opt/openevolve/bin/python - <<'PY'
import numpy, scipy
print("numpy", numpy.__version__, numpy.__file__)
print("scipy", scipy.__version__, scipy.__file__)
PY
```

## 2. Circle Packing 예제 준비

로컬 repo의 `openevolve/examples/circle_packing`을 서버에 복사한다.

권장 위치:

```text
~/openevolve_tutorial/circle_packing
```

필수 파일:

```text
initial_program.py
evaluator.py
config_tutorial.yaml
```

튜토리얼용 evaluator는 기존 예제와 달리 AlphaEvolve reported value인 `2.635`로
normalize하지 않는다. 기본 score는 raw objective와 직접 일치시킨다.

```python
combined_score = actual_sum if valid else 0.0
```

필요하면 `reference_ratio = actual_sum / 2.635`를 보조 지표로 표시할 수 있지만,
OpenEvolve가 selection에 쓰는 `combined_score`는 raw `sum_radii`를 사용한다.
이렇게 해야 "2.635가 진짜 optimum이라는 보장은 없다"는 점과 "우리가 실제로
최대화하는 것은 반지름 합"이라는 점이 명확해진다.

기존 `config_phase_1.yaml`은 4개 worker/island를 사용하므로, 20명 튜토리얼에는
그대로 쓰지 않는 편이 안전하다. 아래처럼 튜토리얼용 config를 따로 둔다.

```yaml
# ~/openevolve_tutorial/circle_packing/config_tutorial.yaml
max_iterations: 10
checkpoint_interval: 1
log_level: "INFO"

llm:
  primary_model: "gpt-oss:20b"
  primary_model_weight: 1.0
  secondary_model: "gpt-oss:20b"
  secondary_model_weight: 0.0
  api_base: "http://localhost:11434/v1"
  api_key: "ollama"
  temperature: 0.7
  top_p: 0.95
  max_tokens: 2048
  timeout: 600

prompt:
  system_message: |
    You are an expert mathematician specializing in circle packing problems
    and computational geometry. Improve a constructor function that produces
    26 circles in a unit square, maximizing the sum of their radii. Keep the
    output as valid Python code and preserve the run_packing() interface.
  num_top_programs: 3
  use_template_stochasticity: true

database:
  population_size: 20
  archive_size: 10
  num_islands: 1
  elite_selection_ratio: 0.3
  exploitation_ratio: 0.7

evaluator:
  timeout: 60
  cascade_evaluation: false
  parallel_evaluations: 1
  use_llm_feedback: false

diff_based_evolution: false
allow_full_rewrites: true
```

중요한 운영 값:

```text
num_islands: 1
parallel_evaluations: 1
cascade_evaluation: false
checkpoint_interval: 1
max_tokens: 2048 또는 4096
max_iterations: dashboard 선택값. 기본 5 또는 10, 긴 run은 queue 대기 시간을 표시하고 허용
```

이 설정은 참가자별 동시 LLM 요청 수를 줄이고, visualization 업데이트 빈도를 높인다.
`api_key: "ollama"`를 config에 직접 넣는 이유는 dashboard가 OpenEvolve를
subprocess로 실행할 때 `OPENAI_API_KEY` 환경변수 전파에 의존하지 않기 위해서다.
`cascade_evaluation: false`로 두는 이유는 score mode를 `evaluate()` 한 곳에서
명확하게 통제하기 위해서다. 기존 circle packing 예제의 cascade stage 함수들은
`2.635` 기준 normalized score를 반환하므로, raw `sum_radii` 튜토리얼과 함께 쓰면
selection score가 문서의 설명과 달라진다. cascade를 다시 켜려면 `evaluate()`,
`evaluate_stage1()`, `evaluate_stage2()`를 모두 같은 raw-score 정책으로 수정하고
threshold도 raw score scale에 맞춰 별도로 검증한다.

## 2.1 Customization Tiers

참가자에게 열어줄 customization은 세 단계로 나눈다. 서버는 자유 입력을 받지
않고, 미리 정의된 dropdown/slider 값만 받아서 template 파일을 생성한다.
이 범위는 튜토리얼 중 모든 조합을 하나씩 설명하기 위한 것이 아니라, 참가자가
관심 있는 방향을 선택해 볼 수 있게 하기 위한 것이다. 대신 dashboard에 노출하는
선택지는 미리 template로 고정한다. 발표 전에는 각 template family, 각 score mode,
그리고 n 변경처럼 evaluator shape가 바뀌는 고위험 선택지를 최소 1회 smoke test한다.

### Beginner

OpenEvolve 실행 설정만 바꾼다. 문제 정의와 evaluator는 고정한다.

```text
iterations: 3 / 5 / 10 / 20
temperature: 0.3 / 0.7 / 1.0
max_tokens: 2048 / 4096
prompt style: conservative / balanced / creative
initial layout: ring / grid / hex-like
```

`temperature`는 LLM sampling randomness를 조절하고, `prompt style`은 지시문의
제약 강도를 바꾼다. 둘 다 탐험성에 영향을 주지만 dashboard에서는 다른 의미의
knob로 표시한다.

서버 준비물:

```text
config_tutorial.yaml.j2
initial_program_ring.py.j2
initial_program_grid.py.j2
initial_program_hex.py.j2
```

### Intermediate

문제 크기와 score mode를 바꾼다.

```text
n: 10 / 16 / 26
score_mode:
  - hard_valid_sum
  - soft_penalty
  - intentionally_bad_reported_sum
```

서버 준비물:

```text
evaluator.py.j2
initial_program.py.j2
config_tutorial.yaml.j2
```

`n`을 바꾸면 다음이 같이 바뀌어야 한다.

```text
initial_program.py: n and initial layout
evaluator.py: expected centers/radii shape
config_tutorial.yaml: prompt text
visualization: title and labels
```

`reference_ratio = actual_sum / 2.635`는 n=26 전용 보조 지표다. n=10 또는 n=16을
열 때는 raw `sum_radii`만 표시하거나, 해당 n에 맞는 별도 reference를 명확히
분리해서 표시한다.

score mode는 안전한 enum으로만 제공한다. 참가자에게 arbitrary Python evaluator
입력을 허용하지 않는다.

권장 score modes:

```python
if score_mode == "hard_valid_sum":
    combined_score = actual_sum if valid else 0.0

elif score_mode == "soft_penalty":
    combined_score = reported_sum - overlap_weight * overlap_penalty - boundary_weight * boundary_penalty

elif score_mode == "intentionally_bad_reported_sum":
    combined_score = reported_sum
```

`intentionally_bad_reported_sum`은 실험용으로만 제공한다. LLM이 score를 해킹해서
겹치는 원, 음수 반지름, 잘못된 reported sum을 만들 수 있음을 보여주는 용도다.

### Advanced

문제 template 자체를 바꾼다.

```text
problem:
  - circle_packing
  - tsp
  - no_isosceles
```

서버 준비물:

```text
tutorial/server/tutorial_server/problems.py
  - circle_packing initial/evaluator/config template
  - tsp initial/evaluator/config template
  - no_isosceles initial/evaluator/config template

tutorial/server/tutorial_server/checkpoints.py
  - stable checkpoint reader
  - best_program.py subprocess executor
  - visualization data extractor for all three problem interfaces
```

OpenEvolve problem template은 공통적으로 세 파일을 만든다.

```text
run_dir/initial_program.py
run_dir/evaluator.py
run_dir/config.yaml
```

dashboard는 `checkpoints.py`로 best program output을 JSON 형태로 추출한 뒤
Streamlit 앱에서 그린다. circle packing은 원을 그리고, TSP는 점과 tour path를
그리고, no-isosceles는 grid point subset을 그린다.

## 3. Ollama Health Check

튜토리얼 시작 전에 서버에서 확인한다.

```bash
curl -s http://localhost:11434/v1/models | python3 -m json.tool
ollama list
```

`gpt-oss:20b`가 보이고 OpenAI-compatible endpoint가 응답해야 한다.

간단한 completion check:

```bash
curl -s http://localhost:11434/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "gpt-oss:20b",
    "messages": [{"role": "user", "content": "Return the word ok."}],
    "max_tokens": 64
  }' | python3 -m json.tool
```

Ollama는 20명 튜토리얼에서 가장 쉽게 병목이 된다. 서버 운영자가 Ollama를
재시작할 수 있다면 다음 값을 미리 검토한다.

```bash
export OLLAMA_NUM_PARALLEL=3
export OLLAMA_KEEP_ALIVE=30m
export OLLAMA_MAX_LOADED_MODELS=1
```

`OLLAMA_NUM_PARALLEL`은 동시에 처리할 generation 수를 정한다. 너무 높이면 각
요청이 모두 느려질 수 있으므로 20B 모델에서는 3부터 확인한다. dashboard의
`max_active_jobs`도 이 값과 맞춘다. 4로 올리고 싶다면 두 값을 함께 올린 뒤
smoke test와 짧은 multi-job test를 다시 실행한다.
`OLLAMA_KEEP_ALIVE`는 모델을 warm 상태로 유지해 첫 요청 지연을 줄인다.

## 4. OpenEvolve Smoke Test

dashboard를 붙이기 전에 서버에서 직접 1 iteration을 실행한다.

```bash
export PYTHONPATH="$HOME/openevolve_pydeps"

/opt/openevolve/bin/openevolve-run \
  "$HOME/openevolve_tutorial/circle_packing/initial_program.py" \
  "$HOME/openevolve_tutorial/circle_packing/evaluator.py" \
  --config "$HOME/openevolve_tutorial/circle_packing/config_tutorial.yaml" \
  --iterations 1 \
  --output "$HOME/openevolve_tutorial_runs/smoke/$(date +%Y%m%d_%H%M%S)" \
  --api-base http://localhost:11434/v1 \
  --primary-model gpt-oss:20b \
  --log-level INFO
```

성공 기준:

```text
- initial program evaluation succeeds
- logs/openevolve_*.log is created
- checkpoints/checkpoint_1/best_program.py is saved
- checkpoints/checkpoint_1/best_program_info.json is saved
- best/best_program.py and best/best_program_info.json are saved after completion
```

1 iteration smoke test가 통과하면 같은 config로 3-5 iterations calibration run을
한 번 더 실행한다. dashboard ETA seed는 예전 실험값이 아니라 이 calibration run의
wall-clock time과 completed iteration 수로 계산한다.

## 5. Visualization 동작 방식

dashboard는 OpenEvolve 내부를 수정하지 않고 output directory를 watch한다.

읽을 파일:

```text
<run_dir>/logs/openevolve_*.log
<run_dir>/checkpoints/checkpoint_*/best_program.py
<run_dir>/checkpoints/checkpoint_*/best_program_info.json
<run_dir>/best/best_program.py
<run_dir>/best/best_program_info.json
```

진행 중 실시간 표시에는 `best/`를 사용하지 않는다. OpenEvolve는 run이 끝날 때
top-level `best/`를 한 번 저장하고, 진행 중 best-so-far 상태는
`checkpoint_interval: 1`일 때 `checkpoints/checkpoint_<iteration>/` 아래에 저장한다.
따라서 dashboard는 checkpoint를 숫자 기준으로 읽되, OpenEvolve가 쓰는 중인
checkpoint를 피하기 위해 stable checkpoint만 렌더링한다. `best/`는 완료 후 최종
상태 확인용으로만 사용한다.

업데이트 루프:

1. `checkpoints/checkpoint_*` 중 stable checkpoint를 찾는다.
2. `<checkpoint>/best_program_info.json`을 읽는다.
3. score 값은 `metrics.combined_score`, `metrics.sum_radii`, `metrics.validity`에서 읽는다.
4. plot x축은 checkpoint directory number 또는 `current_iteration`을 쓴다. top-level
   `iteration`은 best program이 처음 발견된 iteration이라 x축으로 쓰지 않는다.
5. `<checkpoint>/best_program.py`를 별도 subprocess로 실행해서 `run_packing()` 결과를 얻는다.
6. `centers`, `radii`를 원 그림으로 렌더링한다.
7. checkpoint history로 best-so-far score plot을 그린다.
8. log tail은 별도로 파싱해서 invalid 후보, code extraction failure, timeout을 보여준다.

stable checkpoint 조건:

```text
- best_program.py and best_program_info.json both exist
- best_program_info.json parses as valid JSON
- both files have not changed for at least 1-2 seconds
- if no stable checkpoint is available, keep rendering the previous checkpoint
```

best program 실행은 dashboard process 안에서 직접 `import`하지 말고 별도 Python
subprocess로 실행한다. 그래야 후보 코드가 예외를 내도 dashboard가 죽지 않는다.

예시 runner:

```bash
RUN_DIR="$HOME/openevolve_tutorial_runs/alice/20260707_101500"
CHECKPOINT_DIR="$(
python3 - "$RUN_DIR" <<'PY'
import json
import re
import sys
import time
from pathlib import Path

run_dir = Path(sys.argv[1])
now = time.time()
stable = []

for path in (run_dir / "checkpoints").glob("checkpoint_*"):
    match = re.fullmatch(r"checkpoint_(\d+)", path.name)
    if not match:
        continue
    program_path = path / "best_program.py"
    info_path = path / "best_program_info.json"
    if not program_path.exists() or not info_path.exists():
        continue
    if max(program_path.stat().st_mtime, info_path.stat().st_mtime) > now - 2.0:
        continue
    try:
        json.loads(info_path.read_text())
    except Exception:
        continue
    stable.append((int(match.group(1)), path))

if not stable:
    raise SystemExit("no stable checkpoint")

print(max(stable)[1])
PY
)"
PROGRAM_PATH="$CHECKPOINT_DIR/best_program.py"
PYTHONPATH="$HOME/openevolve_pydeps" /opt/openevolve/bin/python - "$PROGRAM_PATH" <<'PY'
import importlib.util
import json
import numpy as np
import sys
from pathlib import Path

program_path = Path(sys.argv[1])
try:
    spec = importlib.util.spec_from_file_location("program", program_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    centers, radii, sum_radii = module.run_packing()
    print(json.dumps({
        "ok": True,
        "centers": np.asarray(centers, dtype=float).tolist(),
        "radii": np.asarray(radii, dtype=float).tolist(),
        "sum_radii": float(sum_radii),
    }))
except Exception as exc:
    print(json.dumps({
        "ok": False,
        "error": type(exc).__name__,
        "message": str(exc),
    }))
    raise
PY
```

dashboard에는 다음 패널을 두면 충분하다.

```text
- Job status: queued / running / completed / failed, queue position, ETA
- Current best score and sum_radii
- Circle packing plot
- Score vs iteration plot
- Valid / invalid / code extraction failure counts
- Latest log tail
- Best source code preview
```

## 6. Job Queue 설계

20명이 동시에 누르면 LLM 요청이 병목이 된다. 기본 OpenEvolve config처럼 1인당
4 worker를 쓰면 20명에서 최대 80개 LLM 요청이 몰린다. 튜토리얼용 config로
1인당 1 request 수준으로 줄여도 20명 동시 시작은 여전히 무겁다.

dashboard에서 active job 수를 제한하되, 참가자의 iteration 선택을 지나치게
좁히지는 않는다. 긴 job은 즉시 거절하지 않고 queue에 넣어 처리한다. 대신
dashboard가 대기 순서와 예상 시작 시간을 명확히 보여주어야 한다.

권장값:

```text
max_active_jobs = 3
per_user_queued_jobs = 1
default_iterations = 5 또는 10
allowed_iterations = 3 / 5 / 10 / 20
```

이전 원격 서버 실험에서는 20 iterations가 약 24분 37초 걸렸지만, 그 값은 기존
실험 config와 당시 Ollama 상태에서 나온 참고값이다. 튜토리얼 config는
`num_islands: 1`, `parallel_evaluations: 1`, `cascade_evaluation: false`이므로
발표 전에 calibration run으로 ETA seed를 다시 잡는다. dashboard는 이후 live job이
완료될수록 최근 완료 job의 평균으로 ETA를 갱신한다.

운영 원칙:

```text
- active job 수만 제한한다.
- queued job은 유지해서 느리더라도 실행되게 한다.
- 한 참가자가 여러 job을 쌓아 queue를 독점하지 못하게 한다.
- 긴 iteration 선택은 허용하되 dashboard에 "expected wait"를 표시한다.
- 발표자는 replay를 설명하면서 queue가 자연스럽게 소화되게 둔다.
```

상태 모델:

```text
queued -> running -> completed
queued -> running -> failed
running -> cancelled
queued -> cancelled
```

job metadata 예시:

```json
{
  "job_id": "alice-20260707-101500",
  "participant": "alice",
  "run_dir": "/home/erdos/openevolve_tutorial_runs/alice/20260707_101500",
  "iterations": 10,
  "score_mode": "hard_valid_sum",
  "status": "running",
  "queue_position": 0,
  "pid": 12345,
  "created_at": "2026-07-07T10:15:00",
  "started_at": "2026-07-07T10:15:03",
  "completed_at": null
}
```

metadata는 단순히 JSON 파일로 관리해도 충분하다.

```text
~/openevolve_tutorial_runs/jobs.json
```

동시성 처리가 복잡해지면 SQLite로 바꾼다. 튜토리얼 규모에서는 JSON + file lock도
충분하다.

OpenEvolve subprocess를 시작할 때는 환경변수를 명시적으로 넘긴다.

```python
env = {
    **os.environ,
    "PYTHONPATH": f"{os.environ['HOME']}/openevolve_pydeps",
    "OPENAI_API_KEY": "ollama",
}
```

config에도 `llm.api_key: "ollama"`를 넣지만, subprocess 환경에도 같은 값을 넣어
버전 차이나 SDK fallback 차이로 인한 실패를 줄인다.

## 7. Dashboard 실행

Streamlit을 쓴다면:

```bash
source ~/tutorial-dashboard-venv/bin/activate
cd ~/openevolve_dashboard
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

외부 포트를 바로 열기 어려우면 참가자가 SSH tunnel로 접근한다.

```bash
ssh -p 7777 -L 8501:localhost:8501 <user>@<server-host>
```

브라우저:

```text
http://localhost:8501
```

서버가 공용 네트워크에 노출된다면 최소한의 접근 제한이 필요하다.

```text
- SSH tunnel만 허용
- 또는 reverse proxy + basic auth
- dashboard에서 shell command 입력을 절대 허용하지 않음
- participant id는 safe slug로 sanitize
```

## 8. 튜토리얼 운영 절차

권장 시간 배분:

```text
0-5분: dashboard 접속, 문제와 화면 구성 설명
5-15분: precomputed replay로 hard_valid_sum / soft_penalty / bad score 비교
15-25분: 참가자들이 live job 제출, queue와 checkpoint 갱신 관찰
25-35분: running/completed job 몇 개를 같이 열어 결과 해석
35-40분: parameter를 바꾸면 무엇을 더 실험할 수 있는지 정리
```

이 흐름에서는 live run이 튜토리얼 중 모두 끝나지 않아도 괜찮다. 참가자의 핵심
경험은 job 제출, queue 진입, running 전환, checkpoint 생성, best-so-far 갱신을
보는 것이다. score function별 비교는 replay가 담당한다.

### 사전 준비

1. Ollama가 살아 있는지 확인한다.
2. `gpt-oss:20b` 모델이 보이는지 확인한다.
3. `openevolve-run` smoke test를 실행한다.
4. dashboard를 실행한다.
5. 발표자용 precomputed run을 score mode별로 준비한다.
6. run directory cleanup script를 준비한다.

cleanup:

```bash
rm -rf "$HOME/openevolve_tutorial_runs"/*
mkdir -p "$HOME/openevolve_tutorial_runs"
```

### 참가자 안내

1. dashboard URL 접속
2. 이름 입력
3. score mode와 iterations 선택. 기본값은 `hard_valid_sum`, 5 또는 10 iterations
4. `Start` 클릭
5. queue 위치와 예상 시작 시간 확인
6. running이 되면 circle plot과 score plot 관찰
7. invalid high-sum 후보가 왜 탈락하는지 log tail에서 확인

### 발표자가 강조할 포인트

```text
- LLM은 후보 코드를 만든다.
- evaluator가 기하 제약을 검증한다.
- sum_radii가 커도 overlap, negative radius, outside square면 score 0이다.
- score function 설계가 잘못되면 LLM은 쉽게 reward를 해킹한다.
- 튜토리얼 기본 score는 normalized ratio가 아니라 raw valid sum_radii다.
- AlphaEvolve의 2.635는 reference일 뿐, optimum으로 가정하지 않는다.
```

## 9. Fallback 계획

서버가 느려지거나 queue가 길어질 경우에도 live queue는 가능한 한 유지한다.
fallback의 목적은 job을 없애는 것이 아니라, 튜토리얼 설명을 replay 중심으로
전환해서 대기 시간을 흡수하는 것이다.

1. dashboard 상단에 queue 지연 상태를 표시한다.
2. 발표자용 precomputed run을 dashboard에서 replay한다.
3. 새 job은 계속 접수하되 예상 대기 시간을 보여준다.
4. 서버가 불안정하면 `max_active_jobs`를 1 또는 2로 낮춘다.
5. 새 job의 권장 iteration 기본값만 5에서 3으로 낮춘다. 이미 queued된 job은
   참가자가 직접 취소하지 않는 한 유지한다.
6. Ollama나 dashboard가 불안정하면 새 job 접수만 일시 중지하고 현재 running job을
   완료시킨다.

fallback replay에 필요한 파일:

```text
logs/openevolve_*.log
checkpoints/checkpoint_*/
best/best_program.py
best/best_program_info.json
```

## 10. 확인된 실험 결과 요약

원격 서버에서 20 iterations를 실제로 실행한 결과:

```text
run_dir: /home/erdos/openevolve_circle_remote_20_20260707_095026
wall-clock: 약 24분 37초
records: 20/20
valid: 11
invalid geometry / zero score: 6
code extraction failure: 3

best:
  iteration: 4
  sum_radii: 2.49996
  combined_score: 0.9487514231
  validity: 1.0
```

주의: 위 실험은 기존 normalized evaluator와 당시 config로 실행했다. 튜토리얼용
raw evaluator와 `cascade_evaluation: false`로 같은 해를 평가하면
`combined_score = 2.49996`이 된다. dashboard에서는 raw `combined_score`를 기본으로
보여주고, AlphaEvolve reported value 대비 비율이 필요하면 n=26에서만 별도
`reference_ratio`로 표시한다. 위 wall-clock 값은 운영 감각을 잡기 위한 참고값이며,
dashboard ETA seed는 튜토리얼 config calibration run으로 다시 측정한다.

반복적으로 관찰된 invalid 후보:

```text
sum_radii = 2.635
reason: circles overlap
score: 0
```

이 사례는 튜토리얼에서 score function/evaluator의 필요성을 설명하기에 좋다.

## 11. 남은 구현 작업

서버 준비 문서 기준으로 아직 구현해야 할 것은 다음이다.

```text
1. ~/openevolve_tutorial/circle_packing 고정 디렉터리 정리
2. raw sum_radii 기반 evaluator.py 생성
3. config_tutorial.yaml 생성
4. beginner/intermediate/advanced template 파일 생성
5. Streamlit dashboard 작성
6. job queue 작성
7. checkpoint 기반 best_program.py visualization runner 작성
8. health check UI 작성
9. score mode별 precomputed replay run 준비
10. 발표 당일 cleanup / restart 절차 테스트
```

이 중 1-9까지 준비해야 40분 튜토리얼에서 live queue와 score mode replay를 모두
안정적으로 보여줄 수 있다. 1-7만 있으면 live run 관찰은 가능하지만, score function
비교 설명은 약해진다.
