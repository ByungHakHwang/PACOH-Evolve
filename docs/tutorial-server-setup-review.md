# `tutorial-server-setup.md` 견고성 검토

> 대상 문서: [`tutorial-server-setup.md`](./tutorial-server-setup.md)
> 검증 기준: 로컬 클론 OpenEvolve **0.3.0** 소스 코드와 대조 (서버는 0.2.27 — F 항목 참조)
> 작성일: 2026-07-07

## 총평

전체 골격(브라우저 → dashboard → 서버 subprocess → ollama, output 디렉터리 watch,
job queue, 보안 sanitize)은 **설계가 탄탄**하다. 문서의 config 스키마·파일 경로·
`run_packing()` 인터페이스는 실제 코드와 대부분 정확히 일치한다.

다만 **"실시간으로 결과가 바뀌는 걸 지켜본다"는 이 튜토리얼의 핵심 목표**를 깨뜨릴 수
있는 문제 2개(A, B)와, 운영상 현실성 문제 1개(C)가 있다.

---

## ✅ 코드로 검증되어 맞는 부분

- `run_packing() → (centers, radii, sum_radii)` — 문서 §5 visualization runner와 일치
  (`examples/circle_packing/initial_program.py:92`)
- Config 스키마(top-level `max_iterations`/`checkpoint_interval`, `llm.primary_model`,
  `database.num_islands`, `evaluator.cascade_*`) — 0.3.0 예제 `config_phase_1.yaml`과
  **동일 구조**
- `cascade_evaluation: true` + `thresholds: [0.5, 0.75]` — evaluator에 `evaluate_stage1`,
  `evaluate_stage2`가 실제로 존재 (`examples/circle_packing/evaluator.py:281,335`)
- metric 이름(`combined_score` / `sum_radii` / `validity` / `target_ratio` / `eval_time`)
  — evaluator 반환값과 일치
- 출력 구조 `logs/`, `checkpoints/checkpoint_*/`, `best/` — `openevolve/controller.py:197,458,563` 확인
- `secondary_model_weight: 0.0` → **secondary 모델이 아예 models 리스트에서 제외됨**
  (`openevolve/config.py:139-141`) → 의도한 "참가자당 1 request" 정확히 달성
- CLI 플래그(`--config` / `--iterations` / `--output` / `--api-base` / `--primary-model` / …)
  모두 존재

---

## 🔴 반드시 고쳐야 할 것

### A. `best/`는 run이 끝날 때 딱 한 번만 쓰인다 — 실시간 시각화가 안 됨 (최우선)

문서 §5의 업데이트 루프(2~4단계)는 `best/best_program_info.json` +
`best/best_program.py`를 읽는다. 그런데 `_save_best_program()`은 evolution 종료
시점(`controller.py:419`, "Evolution complete")에 **딱 1회** 호출된다. 즉 **run
진행 중에는 `best/`가 존재하지 않거나 갱신되지 않는다.**

진행 중 매 iteration 갱신되는 실시간 신호는 `checkpoints/checkpoint_N/` 쪽이다
(`checkpoint_interval: 1`이라 매 iter마다 `best_program_info.json` + `best_program.py`
기록, `controller.py:482`).

**수정:** 실시간 루프는 **가장 최신 `checkpoints/checkpoint_*/`를 watch**하도록 바꾸고,
`best/`는 완료 후 최종 상태 표시용으로만 사용한다. (문서는 checkpoints도 "읽을 파일"에
나열은 해뒀지만, 정작 update loop는 `best/`를 읽게 서술돼 있어 방향이 거꾸로다.)

### B. `api_key`가 config 파일 경로에서 누락되어 job이 시작조차 못할 수 있음

`load_config()`는 **config 파일을 넘기면 `OPENAI_API_KEY` env를 적용하는 코드(line 505)를
건너뛴다** — env 반영은 config 파일이 *없을* 때(`else` 분기)만 일어난다
(`config.py:496-505`). CLI에 `--api-key` 플래그도 없고, 문서의 `config_tutorial.yaml`에도
`api_key`가 없다. → 모델별 `api_key = None`.

이게 그래도 도는 유일한 이유는 openai Python SDK가 `api_key=None`일 때 **자기 스스로**
`os.environ["OPENAI_API_KEY"]`로 fallback하기 때문이다. 그런데 이건 **dashboard가 띄우는
subprocess의 환경변수**에 `OPENAI_API_KEY`가 있어야만 성립한다. 문서 §4 smoke test는
셸에서 export하지만, §5–7의 job_manager / `subprocess.Popen`에는 "env를 넘겨라"는
언급이 없다. streamlit을 export 안 한 셸에서 띄우면 → 자식 프로세스에 전파 안 됨 →
`The api_key client option must be set`로 즉시 실패.

**수정(권장):** env 의존을 없애고 `config_tutorial.yaml`의 `llm:` 블록에
`api_key: "ollama"`를 직접 명시. (`config.py:169-183`에서 llm-level `api_key`가 각 모델로
정상 전파됨을 확인.) 또는 job_manager의 `Popen(..., env={**os.environ, "OPENAI_API_KEY": "ollama"})`를
문서에 명시.

---

## 🟠 운영 현실성 (설계 자체 문제는 아니나 튜토리얼 성패를 좌우)

### C. 50분 세션 안에 20명 live run을 소화할 수 없음

문서 §10 실측: **20 iter에 24분 37초 ≈ 74초/iter** (gpt-oss:20b). 튜토리얼 config(10 iter)면
~12분/run. `max_active_jobs = 3~4`로 20명을 돌리면 큐 배출에 대략 (20 / 3.5) × 12 ≈
**68~80분** — 세션을 넘긴다. 게다가 서버엔 `gpt-oss:20b` / `:latest`뿐이라 **더 작은
모델로 갈아탈 여지도 없어** run 시간이 고정이다.

문서 §9에 fallback(replay)이 있지만 *예비책*으로만 다뤄진다. 이 산수를 보면 현실적으로
replay가 기본 경로여야 한다.

**수정:**
1. 발표자 precomputed run replay를 **기본**으로(전원 공유 관람) + 원하는 사람만 개인 run 큐잉.
2. 기본 iterations 3~5로.
3. 예상 소요시간(1인 ~12분, 동시 3~4명)을 문서 상단에 명시.

---

## 🟡 사소하지만 고치면 좋은 것

| # | 위치 | 내용 |
|---|---|---|
| D | §5 step 2 | `best_program_info.json`에서 `combined_score` / `sum_radii`는 **`metrics.` 아래 중첩**, `iteration`만 top-level. 문서는 셋 다 top-level처럼 읽으라고 서술 → 그대로 짜면 `None` / KeyError |
| E | §6 | ollama 서버측 동시성 튜닝 언급 없음. 3~4 동시 요청 + 20b면 `OLLAMA_NUM_PARALLEL`, `OLLAMA_KEEP_ALIVE`(모델 warm 유지), `OLLAMA_MAX_LOADED_MODELS` 설정 권장 |
| F | §서두 | 서버는 OpenEvolve **0.2.27**, 이 발표 폴더 로컬 클론은 **0.3.0**. 스키마는 호환되나 버전 skew 명시/고정 권장 |
| G | config | `primary_model: "gpt-oss"`(bare)는 ollama에서 `:latest`로 해석됨. 모호함 피하려면 `gpt-oss:20b`로 핀 고정 |
| H | §5 runner | `centers.tolist()`는 numpy 가정 — 진화된 후보가 list를 반환하면 실패(subprocess 격리라 dashboard는 안 죽음). `np.asarray()`로 강제 + 예외 가드 권장 |
| I | §5/§8 | "best 점수 상승 곡선"은 checkpoint(단조 best-so-far)에서, "invalid 후보 탈락" 스토리는 log tail(개별 후보 점수)에서 — 두 데이터 소스를 분리 서술하면 dashboard 설계가 명확 |

---

## 결론

구조와 설계 자체는 견고하다. 다만 **A(실시간이 실제로는 종료 시 1회)**와
**B(api_key subprocess 전파)**는 목표 경험을 직접 깨뜨리므로 반드시 반영해야 하고,
**C(throughput)**는 운영 시나리오를 replay 기본으로 재구성해야 한다.

### 다음 단계 제안
- A·B·C를 반영해 `tutorial-server-setup.md` 개정
- 검증된 `config_tutorial.yaml`(api_key 포함, checkpoint 기반 시각화 전제) 작성
