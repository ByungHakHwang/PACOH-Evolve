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
