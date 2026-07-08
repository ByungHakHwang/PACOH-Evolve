# `tutorial-server-setup.md` 견고성 검토

> 대상 문서: [`tutorial-server-setup.md`](./tutorial-server-setup.md)
> 검증 기준: 로컬 클론 OpenEvolve **0.3.0** 소스 코드와 대조 (서버는 0.2.27 — F 항목 참조)
>
> - **1차 검토** (초판 대상, 2026-07-07): 아래 A~I. → 개정판에 거의 전부 반영됨.
> - **2차 검토** (raw-score + Customization Tiers 개정판 대상, 2026-07-07): 문서 맨 아래 참조.

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

---
---

# 2차 검토 — raw-score + Customization Tiers 개정판

> 대상: 위 1차 검토 반영 후 개정된 `tutorial-server-setup.md` (758줄판)
> 검증 기준: OpenEvolve **0.3.0** 소스 + `examples/circle_packing` 실코드 대조
> 작성일: 2026-07-07

## 개정 반영 확인 (긍정)

1차 검토의 A~I가 **거의 전부 정확히 반영**됨:

- **A** — checkpoint 기반 실시간 시각화로 재작성 (§5, 최신 checkpoint를 `sort -V`로 선택)
- **B** — `api_key: "ollama"`를 config에 직접 명시 + job subprocess env에도 이중 주입 (§2, §6)
- **C** — "운영 가정" 섹션 신설, replay 중심 40분 타임라인, queue + ETA 표시 (§운영가정, §8, §9)
- **D** — `iteration`은 top-level, score는 `metrics.*`에서 읽도록 수정 (§5 step 3)
- **E** — `OLLAMA_NUM_PARALLEL` / `KEEP_ALIVE` / `MAX_LOADED_MODELS` 추가 (§3)
- **F** — 서버 0.2.27 vs 로컬 0.3.0 skew 명시 (§현재상태)
- **G** — `gpt-oss:20b` 태그 전면 고정
- **H** — visualization runner에 `np.asarray` 강제 + try/except (§5)
- **I** — score plot(checkpoint history)과 invalid 후보(log tail) 데이터 소스 분리 (§5 step 6-7)

새로 추가된 **raw-score evaluator + Customization Tiers(§2.1)**가 아래 신규 리스크를 만든다.

---

## 🔴 [Critical] raw-score 변경이 cascade 구조에서 무효화됨 (§2 · §10)

문서 §2는 evaluator를 `combined_score = actual_sum if valid else 0.0`(raw sum)로 바꾸라 하면서
config는 `cascade_evaluation: true`, `cascade_thresholds: [1.0, 2.0]`를 유지한다.
**이 조합은 의도대로 동작하지 않는다.** 코드 근거:

1. `cascade_evaluation: true`이면 엔진은 `_cascade_evaluate`를 타서 **`evaluate_stage1` /
   `evaluate_stage2`만 호출**하고, top-level `evaluate()`는 stage 함수가 있으면 **호출하지 않는다**
   (`openevolve/evaluator.py:163-165, 388-389, 396, 437`).
2. 문서가 보여준 스니펫은 `evaluate()` 쪽(`examples/circle_packing/evaluator.py:254`)에 해당한다.
   정작 채점하는 `evaluate_stage1`은 **정규화 값**을 낸다 — `combined_score = actual_sum / 2.635`
   (`evaluator.py:311`).
3. threshold는 combined_score를 **정규화 없이 직접 비교**한다: `float(score) >= threshold`
   (`evaluator.py:689`).

**실제 벌어지는 일:**

- stage1이 정규화 상태(좋은 packing ≈ 2.5/2.635 ≈ **0.95**)인데 threshold[0]=**1.0** →
  `0.95 >= 1.0` = False → **모든 후보가 stage1에서 걸려 stage2가 안 돌고**, 화면엔 raw sum이
  아니라 **0.95(정규화 비율)**가 표시된다.
- §10의 기대치("raw evaluator로 combined_score = 2.49996")와 **정면 모순**되고, 튜토리얼의
  핵심 메시지("최대화하는 건 raw 반지름 합, 2.635는 optimum 아님")가 무너진다.
- 세 score_mode(§2.1) 모두 같은 함정 — 채점 로직이 `evaluate()`가 아니라 stage 함수에 있기 때문.
- 보강: `soft_penalty`는 `reported_sum - penalties`라 **음수**가 나올 수 있어 threshold 1.0에서
  전부 컷. `intentionally_bad_reported_sum`도 채점이 `evaluate()`에만 있으면 cascade에선 안 먹음.

**권고 (가장 깔끔): `cascade_evaluation: false`.**

- n=26 단일 평가가 ~0.6초라 cascade 이점이 사실상 없음(§10 eval_time).
- 그러면 문서가 보여준 `evaluate()` 한 곳 수정이 **그대로 유효**해지고, threshold 스케일 함정도
  사라지며, 세 score_mode도 서술대로 동작한다.
- cascade를 유지하려면 `evaluate` / `evaluate_stage1` / `evaluate_stage2` **세 곳 모두** raw로
  바꾸고 threshold를 raw 스케일(예: `[0.5, 1.5]`)로 재설정 + 문서에 명시해야 한다.

---

## ⚙️ [High] 구현 범위가 40분 준비 대비 과도함 (§2.1 · §11)

개정판 스코프: **3 tier × (3 score_mode + 가변 n + ring/grid/hex 시드 + TSP 문제) + Jinja2 템플릿화**.
§11은 10개 항목으로 나열하고 "1-9까지 준비해야 안정적"이라 한다. 그러나:

- **n 변경은 evaluator 수술** — `evaluate_stage1`에 `centers.shape == (26, 2)`가 **하드코딩**
  (`evaluator.py:297`). n=10/16마다 shape 체크·시드·프롬프트를 바꾼 템플릿 + **각각 smoke test** 필요.
- **ring/grid/hex 시드 3종**은 각각 n=26 유효 packing(겹침 없음·단위정사각형 내부)이어야 함.
- **TSP(Advanced)**는 인터페이스(`run_packing` ≠ TSP)·evaluator·visualize가 전부 다른 **사실상
  두 번째 튜토리얼**.
- 위 Critical에서 보듯 채점은 미묘. 조합(n×score_mode)마다 검증 필요 → 준비 시간 빠듯하면
  **검증 안 된 조합이 당일 터질** 위험.

**권고 — "최소 실행 가능 튜토리얼" 계층화:**

1. (반드시) **Beginner tier + `hard_valid_sum` + score_mode replay 3종**. 핵심 경험
   (제출→queue→checkpoint 갱신, evaluator의 invalid 거부) 전부 전달됨.
2. (시간 남으면) Intermediate score_mode **live 선택**.
3. (별도 후속) 가변 n, TSP — 이번엔 **replay 데모로만**.

---

## 🎓 [Medium] 교육 설계상 애매한 지점

- **노브 중복**: Beginner에 `temperature`(0.3/0.7/1.0)와 `prompt style`
  (conservative/balanced/creative)이 **둘 다 탐험성**을 조절 → 혼란. 하나로 합치거나 역할 구분.
- **live 선택 vs replay**: §8 타임라인상 score_mode 비교는 **replay가 담당**(5-15분)하고
  live(15-25분)는 대부분 `hard_valid_sum` 기본값 제출 관찰. → Intermediate의 **live score_mode
  선택 UI**는 거의 안 쓰일 수 있음 → 구현 우선순위 낮춰도 됨.

---

## ⏱️ [Medium] 운영·타이밍 정합성

- **ETA 시드값의 config 불일치**: §6은 74초/iter(§10 실측)를 ETA 초기값으로 쓰나, 그 실측은
  **num_islands=4 / parallel_evaluations=4** 원본 config였다. 튜토리얼 config는 **1/1**이라
  처리량 특성이 다름. → smoke test에서 **튜토리얼 config 그대로** 재측정해 ETA 시드 갱신.
- **`max_active_jobs`(3~4) vs `OLLAMA_NUM_PARALLEL`(3) 불일치**: active 4인데 ollama가 3만
  병렬이면 4번째 job 요청이 ollama 큐에서 대기 → iteration stall → ETA 폭주. **두 값 정렬(둘 다 3).**
- **checkpoint 읽기 레이스**: §5 runner가 최신 checkpoint를 OpenEvolve가 **쓰는 도중** 읽으면
  truncated 파일로 exec 실패(서브프로세스라 dashboard는 안 죽지만 패널 깜빡임). → "가장 최신"
  대신 **두 번째 최신** checkpoint 렌더, 또는 두 파일 존재+mtime 안정 확인 후 렌더.

---

## 🟡 [Low] 기타 정확성

| 위치 | 내용 |
|---|---|
| §5 step 3·6 | checkpoint JSON `iteration`은 그 프로그램의 **출생 iteration**이라 checkpoint 번호와 다를 수 있음(예제 json은 `iteration:0`, `generation:10`). score-vs-iteration **x축은 디렉터리 번호(checkpoint_N)** 사용 권장. |
| §4 smoke test | `--secondary-model gpt-oss:20b`는 weight 0.0이라 models에서 제외됨(무의미·무해). 빼도 됨. |
| §2.1 Intermediate | `reference_ratio = actual_sum/2.635`는 n=26 전용. n=10/16에선 의미 없음(raw score로 갔으니 미표시면 그만). |

---

## 결론 (2차)

개정판은 **1차 견고성 지적을 성공적으로 반영**했고 운영안도 현실적으로 재구성됐다. 다만 새로 넣은
**raw-score 변경이 cascade 구조에서 무효화되는 Critical 버그**가 있어 `cascade_evaluation: false`
(또는 stage 함수 전부 수정 + threshold 재설정)로 반드시 바로잡아야 한다. 그리고 **Tiers 스코프가
40분 준비엔 과해서** Beginner+`hard_valid_sum`+replay를 1순위로 잘라내면 리스크 없이 핵심 경험을
전달할 수 있다.

### 다음 단계 제안 (2차)
- `cascade_evaluation: false` 기준으로 검증된 `config_tutorial.yaml` + raw-score `evaluator.py`
  작성 후 smoke test로 실제 검증
- 스코프를 Beginner + `hard_valid_sum` + replay 3종으로 축소한 §2.1 재구성

---

## 3차 — 검증 실험 결과 (2026-07-07)

위 Critical 지적을 반영한 자산을 만들어 **LLM 없이 실제 실행 검증**했다.
산출물은 `tutorial/circle_packing/`, 검증 하네스는 `verify_evaluator.py`.

**실험 구성:** `cascade_evaluation: false` + **단일 `evaluate()` 경로(stage 함수 제거)** +
raw-score + `SCORE_MODE` env(3개 모드). 서버 Ollama에 접근 불가하므로 채점 로직·config
파싱·실 엔진 통합까지만 검증(LLM mutation 반쪽은 서버 smoke test로 이관).

**결과 (모두 PASS):**

- **raw-score 수정이 실제 적용됨**: `hard_valid_sum`에서 `combined_score == sum_radii`(0.9598),
  정규화값 0.3642와 다름. → cascade OFF가 `evaluate()`를 실제로 사용함을 **실 OpenEvolve
  `Evaluator` 경로**(config→Evaluator→`_direct_evaluate`→`evaluate()`)로 확인.
- **3개 score_mode 동작 확인**: 부정 프로그램(겹친 원 + reported 999) →
  `hard_valid_sum` **0**, `intentionally_bad` **999**(hacking 성립), `soft_penalty` **674**
  (999−overlap325, 페널티는 걸리나 reported값을 믿어 여전히 높음 = 오히려 좋은 교육 사례).
- **config 라우팅**: cascade OFF, 단일 모델 `gpt-oss:20b`, `api_key: "ollama"`가 모델까지 전파.
- **실 CLI 1-iteration 실행**: 초기 프로그램 평가 성공 → 출력 구조 `best/` ·
  `checkpoints/checkpoint_1/` · `logs/` 생성(문서 §5와 일치). LLM 호출만 connection error(예상).
  LLM 실패해도 컨트롤러가 graceful 종료 + 체크포인트 저장.

**실험에서 새로 확인된 사실:**

1. **시드 raw sum ≈ 0.96** (문서 §10의 2.49996은 *진화 결과*이지 시드값이 아님). 진화 여유가
   커서 "점진적으로 좋아지는" 시연에는 오히려 유리.
2. **soft_penalty는 weight 1.0에서 여전히 게임된다**(674). "soft reward도 reported값을 믿으면
   안전하지 않다 → validity gate가 필요"라는 메시지로 활용 가능.
3. **score 그래프 x축**: checkpoint JSON의 `iteration`은 프로그램 *출생 iter*(0일 수 있음)이고,
   체크포인트 번호는 별도 필드 **`current_iteration`**에 있음. 대시보드는 `current_iteration`
   (또는 디렉터리 번호)을 x축으로 써야 함(§5 step 3·6 Low 지적의 정확한 필드명).

**결론:** Critical(raw-score×cascade) 문제는 `cascade_evaluation: false` + stage 함수 제거로
**해소되었고 실 엔진 경로에서 재현 검증**됨. 남은 미검증분은 서버 Ollama를 통한 LLM mutation
end-to-end 한 가지이며, `tutorial/circle_packing/README.md`의 smoke test 명령으로 확인하면 된다.

---

# 4차 검토 — `tutorial/server/` 대시보드 구현 리뷰 (2026-07-08)

**대상:** `tutorial/server/` 전체 — `streamlit_app.py`, `tutorial_server/{job_manager,problems,checkpoints}.py`,
`README.md`, `requirements.txt` (+ `tutorial/circle_packing/` 기존 자산과의 일관성).

**방법:** 독립 리뷰어 8개(정적 5 + **실행 기반 3**)를 병렬로 돌려 원시 발견 67건 → 중복 병합 44건.
실행 기반 리뷰어는 생성된 evaluator/프로그램을 실제로 실행하고(치트 프로그램 투입 포함), 가짜
openevolve 명령으로 JobManager를 E2E 구동하고, 실 CLI 1-iteration을 돌려 checkpoint 구조를 대조했다.
서버 버전 v0.2.27 동작은 로컬 클론의 git 태그(`git show v0.2.27:...`)로 소스 대조. 적대적 검증
단계는 시간 관계로 중단했으나, 아래 High 발견 대부분은 **실행 재현 증거**를 확보한 상태다.

> ⚠️ 리뷰 진행 중에도 파일이 수정되고 있었다(`problems.py`에 `facility_location` 문제 추가 등).
> 발견 사항은 2026-07-08 13시 전후 스냅샷 기준이며 **facility_location은 부분 커버리지**다.
> 단, 새 문제의 evaluator가 같은 템플릿 패턴을 따른다면 F01/F02류 구조 결함을 공유할 가능성이 높다.

**심각도 분포: High 13 · Medium 11 · Low 13 · Info 7**

## 🔴 High — A. 점수 체계가 무너지는 결함 (실행 재현됨)

### F01. TSP evaluator 예외 누출 → "크래시한 프로그램이 영구 1등" (`problems.py:583` 부근)
`run_with_timeout`만 try/except 안에 있고 `analyze_tour`·metrics 조립(`float(reported_length)` 등)은
무방비. `tour=None`, 문자열 reported값, ragged 배열이 오면 `evaluate()`가 예외를 던진다.
OpenEvolve는 4회 재시도 후 **`{'error': 0.0}`을 반환**(v0.2.27 `evaluator.py:296`, 0.3.0 동일)하고
fitness는 0.0이 된다. TSP의 정직한 점수는 전 모드에서 음수(시드 n=20: −5.09)이고 `_is_better`는
단순 `>` 비교이므로 **크래시 프로그램이 영구 best** → score plot의 컬럼이 사라지고 깨진 코드가
"Best source"로 전시되며 시각화도 매 refresh마다 실패한다. 같은 evaluator 안에서 서브프로세스
크래시는 −1e9(최악), 후처리 크래시는 0.0(최고)이라는 자기모순도 있음.
**수정:** `run_with_timeout` 이후 전 구간을 try/except로 감싸 `_zero_metrics(-1e9)` 반환.
4개 evaluator 모두 동일 적용. (선택) TSP 점수를 `max(0, 20−length)`처럼 양수로 옮겨 엔진의
0.0 fallback이 절대 이기지 못하게.

### F02. NaN/Inf 무방비 → 기본 모드에서 진화가 조용히 정지 (`problems.py:226` 부근)
`validate_packing`/`compute_penalties`가 `np.isnan`만 검사(`np.isnan(inf)=False`). inf 반지가 오면
기본 모드 `actual_sum_minus_penalty`에서 `inf − 20·inf = NaN`(실행 확인). v0.2.27
`get_fitness_score`는 combined_score 분기에 finite 검사가 없어 NaN/inf가 DB에 들어가고, island
parent sampling의 `random.choices`가 **`ValueError: Total of weights must be finite`** → 이후 모든
iteration 제출이 실패하고 run은 조기 exit 0. **UI에는 아무 에러도 안 보인다.**
**수정:** `np.all(np.isfinite(...))` 검사로 교체 + evaluate() 말미에 `math.isfinite(combined_score)`
클램프(전 evaluator, 전 float metric).

### F18. reported 값 무제한 신뢰 → +1e12 점수, 플롯 파괴 (`problems.py:590` 등) *(Medium이나 A그룹 연관으로 여기 배치)*
soft/intentionally_bad 계열은 reported값을 클램프 없이 사용: 유효한 투어 + `reported_length=-1e12`
→ **combined_score +1e12**(실행 확인), circle의 `reported_sum=1e308`·inf도 그대로 통과(F02와 합류).
한 번 inf가 나오면 이후 모든 거짓말이 동점(inf>inf=False)이라 "점점 과감해지는 해킹" 서사도 멈춘다.
**수정:** 신뢰 분기에서 `np.clip(reported, -1e6, 1e6)` — 여전히 해킹되지만(교육 목적 유지) 유한.

### F19. 동봉된 TSP hacked 프로그램이 데모에서 역효과 (`problems.py:431` 부근)
`tour=zeros(n)` + `reported_length=0.0`은 soft_penalty에서 **−38,000**(정직 −5.09보다 훨씬 나쁨),
negative_length에서 −1,038,000. 이기는 모드는 intentionally_bad 하나뿐이고 그마저 −0.0 vs −5.09로
근소. "soft reward가 해킹당한다"를 보여주려던 파일이 정반대를 시연한다. 진짜 최적 해킹은
**유효 순열 + 큰 음수 reported_length**(위 F18, +1e9 실행 확인).
**수정:** `np.arange(n)` + `reported_length=-999.0`으로 교체하고 어떤 모드를 이기는지 주석 명기.

## 🔴 High — B. 라이브 세션 중 대시보드 마비

### F03. 시각화 무캐시 재실행 (`streamlit_app.py` render_visualization)
LLM이 만든 best_program.py를 **모든 세션의 모든 rerun마다** 서브프로세스로 재실행(기본 timeout 90s,
파일 전체에 `st.cache_data` 없음). F11(선택 리셋) 때문에 20세션 대부분이 같은 최신 job을 보고 있어
동일 프로그램을 동시 중복 실행 — Ollama가 도는 같은 박스에서 CPU 경합. 평가를 통과한 프로그램은
합법적으로 30초까지 걸릴 수 있으므로 "정상" 코드로도 발생.
**수정:** `(program_path, checkpoint 번호/mtime)` 키의 `st.cache_data` + 기본 timeout 15–20s로 인하.

### F04. stdout 전체 JSON 파싱 — print 한 줄이 시각화 영구 파괴 (`checkpoints.py` execute_program)
wrapper가 마지막에 `print(json.dumps(...))` 하고 부모는 `json.loads(result.stdout)`. evolved 코드가
print 하나만 추가해도(20b 모델의 흔한 diff 아티팩트) JSONDecodeError. **비대칭이 핵심:** evaluator는
pickle 파일로 결과를 받아 print 있는 프로그램을 잘 통과시킴 → 그 프로그램이 best가 된 뒤 시각화만
남은 run 내내 실패(재현 완료).
**수정:** `json.loads(result.stdout.strip().splitlines()[-1])` 또는 결과를 temp 파일로 전달
(evaluator의 pickle 프로토콜과 통일). system_message에 "stdout에 print 금지" 한 줄 추가.

### F07. cancel이 글로벌 락을 쥔 채 10–20초 대기 → 전원 프리즈 (`job_manager.py` cancel/_terminate_process)
RUNNING job 취소 시 락을 쥔 채 `killpg(SIGTERM)` + `wait(timeout=10)`. OpenEvolve는 SIGTERM을
graceful shutdown으로 처리(진행 중 LLM 호출 + evaluation 완료 대기, v0.2.27 `controller.py` SIGTERM
핸들러 확인)하므로 10초 초과가 **일상적**. 실측: cancel 중 `jobs()`/`counts()`/`submit()` 9.8초 블록
= 20명 전원 정지. 2번째 `wait(timeout=10)`은 try/except 없음 → TimeoutExpired가 UI로 전파되고 job은
CANCELLING 영구 고착(+ per-user 제한이 CANCELLING을 세므로 그 참가자는 세션 내내 제출 불가).
**수정:** 락 안에서는 상태 변경+process 참조 획득만, 시그널·대기는 락 밖에서. SIGKILL 승급은
worker(이미 readline-EOF + wait로 회수함)에 위임. 마지막 wait에 try/except.

### F08. worker 스레드 예외 가드 전무 → 워커 영구 사망 (`job_manager.py` _worker_loop)
`_run_job`을 감싸는 try/except가 없다. 실증된 트리거 2개: (a) `_write_metadata_unlocked`의
mkdir/write_text가 디스크 quota/권한으로 OSError — **stdout 라인마다 호출**되므로 노출 극대
(재현: PermissionError → 워커 사망, job은 RUNNING 고착, `<defunct>` 좀비, 용량 3→2→1→0);
(b) `text=True`(errors=strict)로 병합된 stdout에서 **비UTF-8 바이트 1개** → readline에서
UnicodeDecodeError(재현 완료). 죽은 워커는 UI 어디에도 표시 안 됨.
**수정:** `_worker_loop`에서 `_run_job`을 try/except로 감싸 job을 FAILED 처리 + process 회수 후
루프 지속. Popen에 `errors='replace'`. metadata 쓰기는 best-effort로.

### F09. 상태 인메모리 only + orphan 프로세스 (`job_manager.py`)
`_jobs`/`_pending`은 메모리뿐, `job_metadata.json`은 쓰기만 하고 아무도 안 읽음(PID도 기록 안 함).
`start_new_session=True`라 대시보드 Ctrl-C/크래시 후에도 openevolve 프로세스들이 **보이지 않게
Ollama를 계속 사용**. README §10의 "MAX_ACTIVE_JOBS=1로 재시작" 처방을 따르면 실부하는 1+3이 되어
오히려 악화, §12의 "subprocess는 dashboard와 함께 관리된다"는 사실과 다름. 두 번째 streamlit
인스턴스를 띄우면 독립 매니저가 하나 더 생겨 제한·부하 2배(재현: 같은 participant 양쪽 접수됨).
**수정:** metadata에 PID/pgid 기록 + 기동 시 run_root 스캔으로 stale run 표시/청소, atexit/SIGINT
훅에서 killpg, run_root lockfile로 이중 기동 방지. README §10/§12 정정.

## 🔴 High — C. 참가자 20명 UX 트랩

### F06. 기본 participant id "guest" → 사실상 1명만 제출 가능 (`streamlit_app.py`)
모든 세션이 "guest"로 프리필 + slug 기준 전역 per-user 제한 1 → 첫 제출자 외 전원이
`guest already has a queued or running job` 에러(해결 방법 미안내). F05의 리로드가 고친 id를 다시
guest로 되돌려 재장전.
**수정:** 빈칸 기본 + 미입력 시 제출 차단, 또는 세션별 `user-xxxx` 랜덤 프리필. 에러 문구에
"participant id를 바꾸세요" 추가.

### F05. Auto refresh = 1회용 전체 리로드, 세션 초기화 (`streamlit_app.py` + README §9)
`<meta http-equiv='refresh'>`는 브라우저 페이지 리로드 → **새 Streamlit 세션**(session_state 전멸:
id→guest, 선택 리셋). 리로드 후 `auto_refresh` 체크박스도 기본값 False로 돌아가 **딱 1회 새로고침
후 기능이 스스로 꺼진다.** README는 주기적 갱신으로 설명하고 있어(§9) 문서도 오류.
**수정:** `st.fragment(run_every=…)`(Streamlit ≥1.37, requirements 상향) 또는
streamlit-autorefresh 컴포넌트로 교체. README §9/§10 해당 서술 정정.

### F11. Inspect selectbox가 남의 최신 job으로 리셋 (`streamlit_app.py` render_job_list)
key 없는 selectbox + status가 포함된 라벨 = 옵션이 바뀔 때마다 위젯 identity가 바뀌어 index 0
(= **전역 최신 job**)으로 리셋. 누가 제출하거나 상태가 바뀔 때마다 모든 참가자의 상세 패널이
남의 job으로 점프 — intentionally_bad의 999점을 자기 결과로 오인하는 시나리오가 자연 발생.
**수정:** 안정된 job id 리스트 + `key` + `format_func`, 선택 id를 session_state에 저장,
기본 선택은 "그 세션 참가자의 최신 job".

### F12. 아무나 남의 job 취소 가능 (`streamlit_app.py` Cancel 버튼)
소유권 검사 없음 + F11의 선택 리셋과 결합해 **실수 취소**가 구조적으로 유발됨(클릭과 rerun 사이에
선택이 남의 job으로 바뀌는 창). 고의 방해도 가능.
**수정:** 상세/취소 뷰를 세션 participant 소유 job으로 스코프(전역 테이블은 읽기 전용 유지),
최소한 취소 시 participant 일치 확인.

### F13. form 안의 custom-N 체크박스 — 입력칸이 안 나타나고 기본값으로 제출 (`streamlit_app.py`)
Streamlit form 내부 위젯은 제출 전까지 rerun을 일으키지 않으므로 체크해도 number_input이 나타나지
않음. 제출하는 rerun에서야 생성되며 그때 **기본값(16/20/8/…)이 사용**되고 사용자가 고른 dropdown
값은 버려짐 + per-user 제한 때문에 정정 재제출도 막힘.
**수정:** custom-N 체크박스를 form 밖(Problem selectbox 옆)으로 이동, 또는 체크박스+selectbox 쌍을
bounded `st.number_input` 하나로 통합.

### F10. iterations 50 선택 가능 — 워커 3개를 세션 내내 점유 (`problems.py` ITERATION_OPTIONS)
자체 실측(§10, 74s/iter) 기준 50 iterations ≈ 60분+. wall-clock 제한도 없음. 3명이 50을 고르면
이후 모든 job이 세션 끝까지 queued.
**수정:** 세션용 옵션을 (1,2,3,5,10)으로 캡(20/50은 운영자 env로 게이트) 및/또는 `_run_job`에
subprocess wall-clock timeout.

## 🟡 Medium (11건 요약)

- **F14** cancel 유실 레이스: status=RUNNING인데 `process=None`인 창(Popen 완료 전)에 cancel이 오면
  False 반환 + UI는 반환값 무시 → 클릭이 조용히 증발(50회 중 7회 자연 재현). → 그 창에서도
  CANCELLING 마킹 + `_run_job`이 process 할당 직후 재확인; UI에서 False면 st.warning.
- **F15** `visualization_env`가 pydeps(= `/opt/openevolve` 파이썬용으로 빌드된 numpy)를 대시보드
  venv 앞에 PYTHONPATH 주입 → 두 인터프리터 마이너 버전이 다르면 **시각화 전멸**(ImportError).
  시각화 서브프로세스에는 pydeps가 애초에 불필요(대시보드 venv에 numpy 있음). → 주입 제거.
- **F16** LLM 전멸(오프라인/모델명 오타)이어도 openevolve-run은 **exit 0** → 전부 COMPLETED로 표시
  (실행 확인: "All 4 attempts failed" 후 "Evolution complete!" exit 0). health_check는 모델명을
  `/models` 목록과 대조하지 않음. → 로그의 실패 패턴 스캔 + 모델명 검증 추가.
- **F17** `random_seed` 미설정 → 기본 **42** 고정, LLM `seed` 파라미터로 전파(Ollama 존중) →
  같은 설정의 참가자들이 **사실상 동일한 진화 결과**를 받음. "다 같이 돌려보고 비교" 시나리오가
  무너짐. → CONFIG_TEMPLATE에 job별 seed(예: job id 해시) 주입.
- **F20** `plot_noiso`가 evolved 프로그램이 반환한 `grid_n`을 무검증으로 사용해 grid_n² 튜플을
  서버 프로세스 안에서 생성 → 거대 grid_n이면 다중초 정지/OOM(측정: 2000→1.9s, 50000→OOM).
  → 신뢰 파라미터 `params.noiso_n`으로 클램프.
- **F21** 전역 pyplot API를 세션 스레드들이 동시 사용(st.pyplot 문서가 락 권고) + 예외 시
  `plt.close` 미도달로 figure 누수. → OO API(Figure+FigureCanvasAgg) 또는 락+finally.
- **F22** health_check(2s timeout HTTP GET)가 **모든 세션의 모든 rerun 최상단**에서 실행 —
  Ollama가 버벅일 때 전 상호작용이 2초씩 느려짐. → `st.cache_data(ttl=10)`.
- **F23** stdout **라인마다** 글로벌 락 잡고 metadata 전체 재작성(truncate-then-write 비원자:
  외부 읽기 19% torn 실측). NFS 홈이면 락 경합 악화 소지. → 상태 변경 시 + 주기적 스냅샷만,
  tempfile+os.replace로 원자화.
- **F24** score mode 문서 분열: standalone은 3모드(기본 hard_valid_sum), 대시보드는 5모드(기본
  actual_sum_minus_penalty, 가중치 20)인데 서버 README에 모드 표 자체가 없음. → 서버 README에
  전 문제 모드 표 추가 + circle_packing README에 "대시보드가 우선" 포인터.
- (원 High였던 **F01/F02/F18/F19**는 A그룹에 통합 서술)

## 🔵 Low (13건, 한 줄씩)

- **F25** 내장 circle evaluator의 PACKING_N 기본 26 ≠ initial 프로그램 기본 16 — env 없이 수동
  재현하면 전부 0점("invalid shapes"). README §11의 재현 절차에 env 필요성 명기 또는 기본값 통일.
- **F26** CANCELLING 상태가 카운터 5칸에 없음(합계 불일치 ~10초).
- **F27** `from_env()`의 int() 무방비(비숫자 env → 페이지 로드마다 traceback), MAX_ACTIVE_JOBS=0의
  silent clamp, 빈 OPENEVOLVE_CMD → argv[0]이 initial_program.py가 되는 황당 실패.
- **F28** `job.error`가 UI 어디에도 표시 안 됨 — Popen 실패 시 "failed + 빈 stdout + 로그 없음"만 보임.
- **F29** Jobs 테이블 'score_mode' 컬럼에 problem_label 전체가 들어감(`active_score_mode()` 헬퍼가
  이미 있는데 미사용).
- **F30** `upstream_target_ratio_n26`이 n≠26에서도 2.635로 나눔(n=16에서 0.427 — 무의미한 "43%").
  모드 선택 시 n=26 강제 권장.
- **F31** no_isosceles가 collinear 삼중점을 전부 제외 → **한 줄 전체가 자명한 유효해**(n=8이면
  size 8). 표준 관례(退化 이등변 포함)와 다름 — 내부 일관성은 있으나 발표 노트에 명시 필요.
- **F32** `allow_full_rewrites`는 두 버전 모두 존재하지 않는 config 키(dacite가 조용히 무시) — 삭제.
- **F33** 기본 iterations=2는 초기 배치(2)가 모두 시드에서 분기 — "1번이 2번의 부모" 서사는 3+부터 참.
- **F34** **scipy는 tutorial/ 어디에서도 import 안 함** — requirements와 README §3/§4/§10의 scipy
  설치·검증 지시는 헛수고 유발(pyyaml도 미사용). 제거 권장.
- **F35** README 보안 서술 공백: 0.0.0.0 무인증(누구나 제출/취소) + LLM 생성 코드를 운영자 권한으로
  무샌드박스 실행. 방화벽/저권한 계정/노출 범위 문단 추가 권장.
- **F36** log_tail이 매 rerun 전체 파일 read 후 슬라이스(수십 MB 로그면 부담) → seek 방식으로.
- **F37** METRIC_KEYS 화이트리스트가 `error`·`eval_time`·`reference_ratio`·`upstream_target_ratio`를
  누락 — n=26 AlphaEvolve 비교라는 핵심 지표가 테이블에 안 나옴 + 실패 원인 열 부재.

## ⚪ Info (7건, 한 줄씩)

- **F38** `OPENAI_API_KEY` env 주입은 --config 사용 시 사문(v0.2.27은 config 없을 때만 env 참조;
  생성 config가 `api_key: "ollama"` 하드코딩) — 키 있는 엔드포인트로 전환 시 함정.
- **F39** safe_slug 특성: 대소문자/구두점 변형이 같은 identity로 병합, 전부 기호인 이름은
  'participant'로 수렴(공유 identity), 한글 통과(런 디렉터리명에 한글).
- **F40** hacked_program.py는 매 run dir에 생성되지만 **어떤 코드 경로/문서도 사용하지 않음** —
  발표자용 데모 명령 한 줄을 README에 추가할 것.
- **F41** v0.2.27은 0.3.0의 MAP-Elites eviction 수정(#454) 이전 — population 12 초과 run에서 검색
  품질 저하만(크래시 없음). 길게 돌리려면 population_size 상향 또는 서버 업그레이드.
- **F42** 문자열 metric(`error`, `example_isosceles_triangle`)은 두 버전 모두 엔진에서 무해함을
  소스로 확인(safe_numeric_average가 필터) — 외부 도구가 맹목 합산할 때만 함정.
- **F43** 설계 문서(docs/tutorial-server-setup.md)와 구현 드리프트: plotly 설치 지시, ring/grid/hex
  레이아웃, iterations 3/5/10/20+ETA 표시, temperature enum, 기본 score_mode 등 — "구현이 우선"
  배너 또는 수치 동기화 필요.
- **F44** plot_noiso가 flat 짝수 리스트를 조용히 (k,2)로 재해석(없는 점 날조 가능),
  plot_tsp는 중복 투어(hacked 전부 0)도 그림 — 후자는 오히려 데모에 유용하나 의도 명시 권장.

## 우선 조치 Top 8 (세션 전 필수)

1. **F06** guest 기본값 제거(빈칸 필수 또는 `user-xxxx` 랜덤)
2. **F01+F02** 4개 evaluator 전신 try/except + isfinite 클램프
3. **F04** execute_program은 stdout 마지막 줄만 JSON 파싱
4. **F03** 시각화 결과 `st.cache_data`(checkpoint 키) + timeout 인하
5. **F05** meta refresh → `st.fragment(run_every=…)` 교체 (+README 정정)
6. **F13** custom-N 체크박스를 form 밖으로
7. **F10** iterations 옵션 (1,2,3,5,10)으로 캡
8. **F07/F08** 락 밖 SIGTERM + worker 예외 가드 + `errors='replace'`

## 결론 (4차)

구조 설계(큐+워커, 문제 파일 생성, checkpoint watch, bounded 입력)는 3차까지의 지적을 잘 반영해
견고한 편이다. 그러나 **(i) evaluator의 예외/비유한값 처리 공백**(F01·F02)은 "정직한 evaluator가
이긴다"는 튜토리얼의 핵심 메시지를 정면으로 배반할 수 있는 결함이고, **(ii) 20명 동시 사용 시나리오
특유의 트랩**(guest 기본값, 선택 리셋, form 내 조건부 위젯, 무캐시 시각화, cancel 프리즈)은 발표
당일에만 드러나는 유형이라 사전 수정이 필수다. Top 8을 반영한 뒤 서버(turing)에서 §7 smoke test를
2~3명 동시 접속으로 리허설하는 것을 권장한다.
