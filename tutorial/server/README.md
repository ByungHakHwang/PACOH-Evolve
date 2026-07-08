# OpenEvolve Tutorial Dashboard

이 dashboard는 Colab이 느리거나 다운되었을 때 사용하는 서버 fallback이다. 참가자는
브라우저로 dashboard에 접속해서 bounded parameter를 고르고 job을 제출한다. 서버는
OpenEvolve를 subprocess로 실행하고, 로컬 Ollama의 OpenAI-compatible endpoint를
통해 LLM을 호출하며, stable checkpoint가 생길 때마다 score plot, 현재 best
configuration, log tail, best source code를 보여준다.

민감정보는 이 문서에 기록하지 않는다. SSH 비밀번호, 개인 API key, 서버 계정 정보는
별도 안전한 채널로 관리한다.

## 지원 예제

Colab notebook과 같은 세 예제를 지원한다.

```text
circle_packing
tsp
no_isosceles
```

공통으로 바꿀 수 있는 값:

```text
iterations
temperature
max_tokens
prompt_style
visualization_timeout
```

문제별로 바꿀 수 있는 값:

```text
circle_packing:
  PACKING_N
  SCORE_MODE

tsp:
  TSP_N
  TSP_SEED
  TSP_SCORE_MODE

no_isosceles:
  NOISO_N
  NOISO_SCORE_MODE
```

사용자 입력은 dropdown, slider, bounded numeric input으로 제한한다. 참가자에게
arbitrary Python evaluator 입력은 허용하지 않는다.

## 전체 실행 흐름

```text
participant browser
        |
        v
Streamlit dashboard
        |
        +-- queue에 job 등록
        +-- run directory 생성
        +-- initial_program.py / evaluator.py / config_tutorial.yaml 생성
        +-- OpenEvolve subprocess 실행
        +-- checkpoint directory watch
        +-- best_program.py를 별도 subprocess에서 실행해 visualization data 추출
        |
        v
Ollama OpenAI-compatible endpoint
        |
        v
gpt-oss:20b or another local model
```

기본값은 동시에 OpenEvolve job 3개만 실행한다. 나머지는 queue에 남아 있다. 이 방식은
20명이 동시에 눌러도 작업을 버리지 않고 순서대로 처리하기 위한 것이다.

## 1. 서버 접속과 repo 위치 확인

서버에 접속한 뒤 repo root로 이동한다.

```bash
ssh <user>@<server-host> -p <port>
cd /path/to/PACOH-Evolve
```

repo가 최신인지 확인한다.

```bash
git status --short --branch
git pull --ff-only
```

튜토리얼 중에는 별도 작업 변경사항이 섞이지 않는 것이 좋다. `git status`에 예상하지
못한 변경사항이 있으면 dashboard를 시작하기 전에 정리한다.

## 2. Ollama 상태 확인

Ollama가 OpenAI-compatible endpoint를 열고 있어야 한다.

```bash
curl -s http://localhost:11434/v1/models | python3 -m json.tool
```

정상이라면 사용할 모델이 보인다. 기본 문서에서는 `gpt-oss:20b`를 사용한다.

짧은 completion도 미리 확인한다.

```bash
curl -s http://localhost:11434/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "gpt-oss:20b",
    "messages": [{"role": "user", "content": "Return the word ok."}],
    "max_tokens": 16
  }' | python3 -m json.tool
```

여기서 응답이 늦거나 실패하면 dashboard를 띄워도 OpenEvolve run이 첫 checkpoint
전에 오래 멈춰 있는 것처럼 보인다.

20명 세션 전에는 Ollama 병렬 처리 값을 보수적으로 둔다.

```bash
export OLLAMA_NUM_PARALLEL=3
export OLLAMA_KEEP_ALIVE=30m
export OLLAMA_MAX_LOADED_MODELS=1
```

이미 Ollama가 systemd service로 떠 있으면 위 값은 service 환경변수로 설정해야 할 수
있다. 직접 shell에서 `ollama serve`를 띄우는 운영 방식이면 같은 shell에서 export한
뒤 시작한다.

## 3. OpenEvolve 경로와 Python dependency 확인

서버에 설치된 OpenEvolve command를 확인한다.

```bash
ls -l /opt/openevolve/bin/openevolve-run
```

위 경로가 없으면 `PATH`에서 찾는다.

```bash
which openevolve-run
```

OpenEvolve evaluator가 `numpy`, `scipy`를 import할 수 있어야 한다. 서버의
OpenEvolve 환경을 직접 수정하기 어렵다면 사용자 홈에 dependency를 설치하고
`OPENEVOLVE_PYDEPS`로 붙인다.

```bash
mkdir -p "$HOME/openevolve_pydeps"
/opt/openevolve/bin/python -m pip install --target "$HOME/openevolve_pydeps" numpy scipy
```

설치 확인:

```bash
PYTHONPATH="$HOME/openevolve_pydeps" /opt/openevolve/bin/python - <<'PY'
import numpy
import scipy
print("numpy", numpy.__version__, numpy.__file__)
print("scipy", scipy.__version__, scipy.__file__)
PY
```

`/opt/openevolve/bin/python` 위치가 다르면 실제 OpenEvolve Python 경로로 바꾼다.

## 4. Dashboard virtualenv 설치

Dashboard는 OpenEvolve와 별도 venv에서 실행한다.

```bash
cd /path/to/PACOH-Evolve
python3 -m venv ~/tutorial-dashboard-venv
source ~/tutorial-dashboard-venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r tutorial/server/requirements.txt
```

설치 확인:

```bash
PYTHONPATH=tutorial/server python - <<'PY'
import streamlit
import pandas
import matplotlib
import numpy
import scipy
import tutorial_server
print("dashboard imports ok")
PY
```

## 5. Dashboard 환경변수 설정

아래 값은 같은 shell에서 `streamlit run`을 실행하기 전에 설정한다.

```bash
export OPENEVOLVE_CMD="/opt/openevolve/bin/openevolve-run"
export OPENEVOLVE_API_BASE="http://localhost:11434/v1"
export OPENEVOLVE_MODEL="gpt-oss:20b"
export OPENEVOLVE_PYDEPS="$HOME/openevolve_pydeps"
export OPENEVOLVE_RUN_ROOT="$HOME/openevolve_tutorial_runs"
export OPENEVOLVE_MAX_ACTIVE_JOBS=3
export OPENEVOLVE_PER_USER_QUEUED_JOBS=1
```

변수 의미:

```text
OPENEVOLVE_CMD:
  OpenEvolve 실행 command. 공백이 있는 command도 shlex 방식으로 split된다.

OPENEVOLVE_API_BASE:
  Ollama OpenAI-compatible endpoint. 보통 http://localhost:11434/v1.

OPENEVOLVE_MODEL:
  OpenEvolve config와 CLI에 들어갈 모델 이름.

OPENEVOLVE_PYDEPS:
  OpenEvolve subprocess의 PYTHONPATH 앞에 붙일 dependency directory.

OPENEVOLVE_RUN_ROOT:
  참가자 job 결과를 저장할 directory.

OPENEVOLVE_MAX_ACTIVE_JOBS:
  동시에 실행할 OpenEvolve subprocess 수. 20B 모델이면 처음에는 1 또는 2로
  smoke test하고, 세션에서는 3 정도를 권장한다.

OPENEVOLVE_PER_USER_QUEUED_JOBS:
  한 participant id가 동시에 가질 수 있는 queued/running job 수.
```

`OPENEVOLVE_CMD`가 `PATH`에서 바로 잡히는 서버라면 다음처럼 쓸 수도 있다.

```bash
export OPENEVOLVE_CMD="openevolve-run"
```

## 6. Dashboard 실행

서버에서 외부 접속을 받을 때:

```bash
source ~/tutorial-dashboard-venv/bin/activate
cd /path/to/PACOH-Evolve

streamlit run tutorial/server/streamlit_app.py \
  --server.address 0.0.0.0 \
  --server.port 8501
```

참가자는 브라우저에서 접속한다.

```text
http://<server-hostname-or-ip>:8501
```

서버 방화벽이나 학내망 정책 때문에 직접 접속이 안 되면 SSH tunnel로 운영자만 먼저
확인할 수 있다.

```bash
ssh -L 8501:localhost:8501 <user>@<server-host> -p <port>
```

그 뒤 운영자 노트북에서:

```text
http://localhost:8501
```

참가자에게 공개하려면 서버의 8501 포트가 참가자 네트워크에서 접근 가능해야 한다.

## 7. Smoke test 절차

튜토리얼 시작 전에 같은 dashboard에서 짧은 job을 문제별로 하나씩 실행한다.

권장 설정:

```text
OPENEVOLVE_MAX_ACTIVE_JOBS=1
iterations=1
temperature=0.4
max_tokens=1024 or 1536
prompt_style=balanced
```

문제별 smoke test:

```text
circle_packing:
  PACKING_N=10 or 16
  SCORE_MODE=actual_sum_minus_penalty

tsp:
  TSP_N=12
  TSP_SEED=0
  TSP_SCORE_MODE=negative_length

no_isosceles:
  NOISO_N=6
  NOISO_SCORE_MODE=size_minus_penalty
```

성공 기준:

```text
1. job이 queued -> running -> completed 또는 적어도 stable checkpoint 생성까지 진행
2. score table에 combined_score가 표시
3. visualization panel에 문제별 그림 표시
4. Best source code expander에 best_program.py 표시
5. OpenEvolve log tail에 치명적인 import error, config parse error, API connection error가 없음
```

첫 checkpoint는 첫 LLM generation과 evaluator 실행이 끝나야 생긴다. 모델이 큰 경우
처음 몇 분 동안 "No stable checkpoint yet"이 보이는 것은 정상일 수 있다.

## 8. Hands-on 세션 운영 권장값

20명, 40분 튜토리얼 기준 권장 시작값:

```text
OPENEVOLVE_MAX_ACTIVE_JOBS=3
OPENEVOLVE_PER_USER_QUEUED_JOBS=1

participant default:
  iterations=2 or 3
  temperature=0.4
  max_tokens=1536
  prompt_style=balanced
```

실제 세션에서는 다음 순서가 안정적이다.

```text
1. 발표자가 dashboard에서 미리 준비한 짧은 run 하나를 보여준다.
2. 참가자에게 participant id를 입력하게 한다.
3. 먼저 circle_packing, iterations=2로 제출하게 한다.
4. queue 상태와 running/completed 변화를 설명한다.
5. checkpoint가 생긴 참가자는 score plot, 그림, best source code를 보게 한다.
6. 여유가 있는 참가자만 TSP 또는 no_isosceles로 두 번째 job을 시도한다.
```

긴 run은 queue에 남겨도 되지만, 40분 hands-on 중에 모두 끝나는 것을 목표로 하지
않는다. score function 비교 설명은 precomputed replay 또는 발표자 run을 기본으로
사용한다.

## 9. Dashboard 사용법

사용자 화면 흐름:

```text
1. Participant name or id 입력
2. Problem 선택
3. Iterations / Temperature / Max tokens / Prompt style 선택
4. Problem-specific option 선택
5. Start OpenEvolve 클릭
6. Jobs table에서 자기 job 선택
7. status, queue position, score history, visualization, log tail 확인
```

`Problem` 선택은 submit form 밖에 있으므로 선택 즉시 problem-specific parameter와 score
function 목록이 바뀐다. 예를 들어 `tsp`를 고르면 `TSP_N`, `TSP_SEED`,
`TSP_SCORE_MODE`만 보이고, `no_isosceles`를 고르면 `NOISO_N`,
`NOISO_SCORE_MODE`만 보인다.

`Auto refresh`는 기본적으로 꺼져 있다. 외부 공유 링크나 프록시를 통해 접속하는
환경에서는 browser-level refresh가 Streamlit form 입력을 제출 전에 초기화할 수
있으므로, job을 제출하기 전에는 켜지 않는다. job 제출 후 진행 상황만 볼 때 켜거나,
대신 `Refresh now` 버튼을 누른다.

Job status 의미:

```text
queued:
  아직 worker를 기다리는 상태.

running:
  OpenEvolve subprocess가 실행 중인 상태.

completed:
  OpenEvolve subprocess가 exit code 0으로 종료.

failed:
  OpenEvolve subprocess가 실패했거나 시작 자체에 실패.

cancelled:
  사용자가 queued/running job을 취소.
```

Dashboard는 top-level `best/` 대신 진행 중에는 `checkpoints/checkpoint_*`를 본다.
`checkpoint_interval: 1`이므로 stable checkpoint가 생성될 때마다 화면이 갱신된다.
Colab처럼 한 cell 안에서 출력이 streaming되는 구조는 아니지만, job 제출 후
`Refresh now`를 누르거나 `Auto refresh`를 켜면 checkpoint 단위로 score table,
score plot, visualization, best source code가 다시 렌더된다.

## 10. Troubleshooting

### Dashboard는 뜨는데 Ollama가 Unavailable

확인:

```bash
curl -s http://localhost:11434/v1/models | python3 -m json.tool
echo "$OPENEVOLVE_API_BASE"
```

`OPENEVOLVE_API_BASE`가 dashboard를 실행한 shell에 export되어 있어야 한다.

### Job이 running인데 checkpoint가 오래 안 생김

가능한 원인:

```text
- LLM generation이 느림
- Ollama queue가 밀림
- max_tokens가 큼
- OPENEVOLVE_MAX_ACTIVE_JOBS가 너무 큼
- 첫 OpenEvolve API call이 retry 중
```

대응:

```bash
export OPENEVOLVE_MAX_ACTIVE_JOBS=1
```

그리고 dashboard를 재시작한 뒤 `iterations=1`, `max_tokens=1024`로 smoke test한다.

### 입력 중 화면이 깜빡이거나 form 값이 초기화됨

`Auto refresh`가 켜져 있으면 browser가 주기적으로 페이지를 reload한다. 외부 링크나
reverse proxy 환경에서는 이 reload가 새 세션처럼 처리되어 form 값이 초기화될 수
있다.

대응:

```text
1. Auto refresh를 끈다.
2. 화면이 한 번 더 reload될 수 있으므로 몇 초 기다린다.
3. 참가자 정보와 parameter를 입력한 뒤 Start OpenEvolve를 누른다.
4. 제출 후에는 Refresh now 버튼을 사용하거나 Auto refresh를 다시 켠다.
```

### evaluator import error

OpenEvolve subprocess가 쓰는 Python에서 `numpy` 또는 `scipy`를 못 찾는 경우가 많다.

확인:

```bash
PYTHONPATH="$OPENEVOLVE_PYDEPS" /opt/openevolve/bin/python - <<'PY'
import numpy
import scipy
print("ok")
PY
```

실패하면:

```bash
mkdir -p "$HOME/openevolve_pydeps"
/opt/openevolve/bin/python -m pip install --target "$HOME/openevolve_pydeps" numpy scipy
export OPENEVOLVE_PYDEPS="$HOME/openevolve_pydeps"
```

### 참가자가 접속할 수 없음

서버에서 dashboard가 떠 있는지 확인:

```bash
curl -I http://127.0.0.1:8501
```

다른 기기에서 안 열리면 서버 방화벽, 학내망, cloud security group, 또는
`--server.address` 설정 문제일 가능성이 높다. 외부 접속을 받으려면
`--server.address 0.0.0.0`로 실행해야 한다.

### 한 사용자가 queue를 독점함

기본값은 한 participant id당 queued/running job 1개다.

```bash
export OPENEVOLVE_PER_USER_QUEUED_JOBS=1
```

참가자에게 participant id를 다르게 바꾸지 말라고 안내한다.

## 11. Run directory 구조

각 job은 `OPENEVOLVE_RUN_ROOT` 아래에 별도 directory를 만든다.

```text
<OPENEVOLVE_RUN_ROOT>/
  <participant>_<problem_label>_<timestamp>_<job_id>/
    job_metadata.json
    problem/
      initial_program.py
      hacked_program.py
      evaluator.py
      config_tutorial.yaml
    openevolve_output/
      logs/
      checkpoints/
      best/
```

Dashboard가 읽는 주요 파일:

```text
openevolve_output/checkpoints/checkpoint_*/best_program.py
openevolve_output/checkpoints/checkpoint_*/best_program_info.json
openevolve_output/logs/*.log
```

`job_metadata.json`에는 dashboard가 관리하는 participant, status, parameter,
recent output이 기록된다.

## 12. 종료와 재시작

Dashboard process를 종료하려면 실행 terminal에서 `Ctrl-C`를 누른다. 실행 중인
OpenEvolve subprocess는 dashboard process와 함께 관리되지만, 강제 종료 후 남은
process가 의심되면 확인한다.

```bash
ps aux | grep -E 'openevolve-run|openevolve-run.py' | grep -v grep
```

필요할 때만 해당 process를 종료한다. 튜토리얼 중에는 실행 중인 참가자 job을
무작정 kill하지 말고 dashboard의 cancel 버튼을 먼저 사용한다.
