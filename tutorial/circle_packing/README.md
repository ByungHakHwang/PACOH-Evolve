# Circle Packing — Tutorial Assets (verified)

OpenEvolve **0.3.0** 기준으로 검증한 튜토리얼용 circle-packing 자산.
`docs/tutorial-server-setup.md`의 2차 검토(Critical: raw-score가 cascade에서
무효화됨)를 반영해 **`cascade_evaluation: false` + 단일 `evaluate()` 경로**로 만들었다.

## 파일

| 파일 | 역할 |
|---|---|
| `initial_program.py` | 진화 시드 (n=26). `run_packing() -> (centers, radii, sum_radii)`. **시드 raw sum ≈ 0.96** (진화 목표 ~2.635, 여유 큼) |
| `evaluator.py` | **raw-score** evaluator. 단일 `evaluate()`만 정의(스테이지 함수 제거). `SCORE_MODE` env로 3개 모드 선택 |
| `config_tutorial.yaml` | `cascade_evaluation: false`, `api_key: "ollama"`, `gpt-oss:20b`, 1 island / 1 parallel |
| `hacked_program.py` | reward-hacking 시연용 "부정" 프로그램 (겹친 원 + 거짓 reported_sum=999) |
| `verify_evaluator.py` | **LLM 없이** 채점·config·실통합을 검증하는 하네스 |

## Score modes (`SCORE_MODE` 환경변수)

- `hard_valid_sum` (기본): `combined_score = actual_sum if valid else 0.0` — 정직한 목적함수. invalid는 무조건 0.
- `soft_penalty`: `reported_sum - overlap_w*overlap - boundary_w*boundary` — 연속 페널티. **reported_sum(거짓)을 믿기 때문에 weight가 낮으면 여전히 게임됨**(교육 포인트).
- `intentionally_bad_reported_sum`: `combined_score = reported_sum` (검증 없음) — reward hacking 시연.

## 검증 결과 (LLM-free, 이 저장소에서 실행 확인됨)

`verify_evaluator.py` 전체 PASS + 실제 CLI 1-iteration 실행 확인:

```
seed baseline raw sum_radii = 0.959764   # 정규화값 0.3642와 다름 = raw score 적용 확인
hacked + hard_valid_sum   -> 0           # 기하 invalid 거부
hacked + intentionally_bad -> 999        # 거짓말이 그대로 점수 (hacking)
hacked + soft_penalty      -> 674        # 999-325, 페널티 적용되나 여전히 높음
config: cascade_evaluation=False, model=gpt-oss:20b, api_key=ollama(전파 확인)
REAL Evaluator path: combined_score == sum_radii (cascade off가 evaluate()를 실제 사용)
```

실제 `openevolve-run.py --iterations 1` 실행 시 출력 구조도 확인:
`best/`, `checkpoints/checkpoint_1/`, `logs/` 생성, checkpoint JSON은
`metrics.combined_score` 중첩 + **`current_iteration`**(체크포인트 번호, 대시보드 x축용).

> LLM 호출(Ollama)만 이 환경에서 미검증. 서버(turing)에서 아래 smoke test로 최종 확인 필요.

### 재실행
```bash
openevolve/.venv/bin/python tutorial/circle_packing/verify_evaluator.py
```

## 서버 smoke test (LLM 포함 최종 확인)

`docs/tutorial-server-setup.md` §4에 대응. 서버(Ollama 稼働)에서:

```bash
export PYTHONPATH="$HOME/openevolve_pydeps"
export SCORE_MODE=hard_valid_sum
/opt/openevolve/bin/openevolve-run \
  "$HOME/openevolve_tutorial/circle_packing/initial_program.py" \
  "$HOME/openevolve_tutorial/circle_packing/evaluator.py" \
  --config "$HOME/openevolve_tutorial/circle_packing/config_tutorial.yaml" \
  --iterations 1 \
  --output "$HOME/openevolve_tutorial_runs/smoke/$(date +%Y%m%d_%H%M%S)" \
  --log-level INFO
```

성공 기준: 초기 프로그램 평가 성공 → LLM이 mutation 생성 → `checkpoints/checkpoint_1/`
+ `best/` 저장. (서버는 0.2.27이므로 config/output 호환성을 여기서 재확인.)

## 대시보드 연동 메모 (검증에서 도출)

- 실시간 표시는 최신 `checkpoints/checkpoint_N/`을 watch (`best/`는 종료 시 1회).
- score-vs-iteration x축: JSON의 `iteration`(프로그램 출생 iter, 0일 수 있음)이 아니라
  **`current_iteration`** 또는 디렉터리 번호 `N`을 사용.
- job subprocess에는 `SCORE_MODE`(및 필요시 `PACKING_N`, `OVERLAP_WEIGHT`, `BOUNDARY_WEIGHT`)를
  env로 넘긴다. `config`에 `api_key: "ollama"`가 있으나 subprocess env에도 `OPENAI_API_KEY=ollama`를 넣으면 안전.
