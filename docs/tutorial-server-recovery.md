# Tutorial Server Recovery Runbook

이 문서는 OpenEvolve tutorial dashboard를 운영하다가 SSH 연결이 끊기거나,
`Ctrl-C`가 Streamlit 대신 SSH session을 끊어 버린 뒤 Ollama가 계속 바쁜 상태로
남았을 때의 복구 절차를 정리한다.

핵심 원칙은 다음 순서다.

```text
1. OpenEvolve subprocess 중지
2. Streamlit dashboard 중지
3. Ollama running model unload
4. 그래도 안 풀리면 Ollama serve 또는 Slurm job 재시작
```

대부분의 경우 Ollama를 직접 죽이기 전에 `openevolve-run`을 먼저 끊으면 충분하다.
Streamlit 자체가 LLM을 오래 잡고 있는 것이 아니라, Streamlit이 띄운
OpenEvolve subprocess가 Ollama에 계속 completion 요청을 보내는 구조이기 때문이다.

## 1. 현재 상태 확인

SSH로 다시 접속한 뒤 현재 사용자 소유 process를 먼저 본다.

```bash
ps -u "$USER" -f | grep -E 'streamlit|openevolve|ollama' | grep -v grep
```

Slurm으로 Ollama나 dashboard를 띄웠다면 job 상태도 확인한다.

```bash
squeue -u "$USER"
```

Ollama가 어떤 모델을 로드하고 있는지도 확인한다.

```bash
ollama ps
```

## 2. OpenEvolve subprocess 중지

먼저 남아 있는 OpenEvolve run을 중지한다.

```bash
pkill -u "$USER" -f openevolve-run
```

몇 초 뒤 다시 확인한다.

```bash
ps -u "$USER" -f | grep -E 'openevolve-run|openevolve-run.py' | grep -v grep
```

아직 남아 있고 종료되지 않으면 강제 종료한다.

```bash
pkill -9 -u "$USER" -f openevolve-run
```

주의: 여러 참가자 job을 같은 계정으로 운영 중이면 이 명령은 그 계정의 모든
OpenEvolve run을 중지한다. 특정 process만 죽여야 하면 `ps` 출력의 PID를 보고
다음처럼 처리한다.

```bash
kill <PID>
sleep 3
kill -9 <PID>
```

## 3. Streamlit dashboard 중지

Streamlit process가 남아 있으면 중지한다.

```bash
pkill -u "$USER" -f 'streamlit run tutorial/server/streamlit_app.py'
```

더 넓게 잡아도 되는 상황이면 다음을 쓸 수 있다.

```bash
pkill -u "$USER" -f streamlit
```

다시 확인한다.

```bash
ps -u "$USER" -f | grep -E 'streamlit|openevolve' | grep -v grep
```

## 4. Ollama running model unload

OpenEvolve를 끊었는데도 Ollama가 계속 바쁘면 running model을 unload한다.

```bash
ollama ps
```

출력에 모델이 보이면 해당 모델을 중지한다.

```bash
ollama stop <model-name>
```

예:

```bash
ollama stop gpt-oss:20b
```

모델 alias가 다를 수 있으므로 반드시 `ollama ps`에 나온 이름을 사용한다.

## 5. Ollama serve 재시작

사용자 권한으로 직접 `ollama serve`를 띄운 경우에만 아래를 사용한다.

```bash
pkill -u "$USER" -f 'ollama serve'
ollama serve
```

`ollama serve`는 foreground process이므로 운영 중에는 `tmux`, `screen`,
`nohup`, 또는 Slurm job 안에서 띄우는 것이 안전하다.

예:

```bash
tmux new -s ollama
ollama serve
```

다른 terminal에서 확인:

```bash
curl -s http://localhost:11434/v1/models | python3 -m json.tool
```

## 6. Slurm으로 Ollama를 띄운 경우

Ollama가 Slurm job 안에서 실행 중이면 `pkill ollama serve`보다 `scancel`이
명확하다.

```bash
squeue -u "$USER"
```

Ollama job의 `JOBID`를 확인한 뒤 취소한다.

```bash
scancel <JOBID>
```

그 다음 기존 Slurm 제출 스크립트로 Ollama job을 다시 제출한다.

```bash
sbatch <ollama-job-script.sh>
```

새 job이 뜬 뒤 endpoint를 확인한다.

```bash
curl -s http://localhost:11434/v1/models | python3 -m json.tool
```

## 7. Dashboard 재시작 전 점검

남은 OpenEvolve와 Streamlit process가 없어야 한다.

```bash
ps -u "$USER" -f | grep -E 'streamlit|openevolve' | grep -v grep
```

Ollama endpoint가 응답해야 한다.

```bash
curl -s http://localhost:11434/v1/models | python3 -m json.tool
```

이후 dashboard를 다시 시작한다.

```bash
source ~/tutorial-dashboard-venv/bin/activate
cd /path/to/PACOH-Evolve

streamlit run tutorial/server/streamlit_app.py \
  --server.address 0.0.0.0 \
  --server.port 8501
```

## 8. 빠른 복구용 최소 명령

상황을 빠르게 풀어야 하고, 현재 사용자 계정의 tutorial job을 모두 중지해도 되는
상황이면 보통 아래 두 줄이면 충분하다.

```bash
pkill -u "$USER" -f openevolve-run
ollama stop gpt-oss:20b
```

그 뒤 Streamlit이 남아 있으면 중지한다.

```bash
pkill -u "$USER" -f streamlit
```

Slurm으로 Ollama를 띄운 경우에는 `ollama stop`으로 해결되지 않거나 다시 바빠질 수
있으므로 `squeue -u "$USER"`와 `scancel <JOBID>`를 우선 확인한다.

## 9. 다음 운영에서 피할 것

- SSH 일반 shell에서 장시간 Streamlit/Ollama를 foreground로 띄우지 않는다.
- 운영용 process는 `tmux`, `screen`, `nohup`, 또는 Slurm 안에서 띄운다.
- Dashboard를 강제 종료하기 전에 가능하면 UI의 cancel 버튼으로 running job을 먼저
  취소한다.
- `pkill -9`는 마지막 수단으로만 쓴다. 먼저 `pkill` 또는 `kill`로 graceful 종료를
  시도한다.
