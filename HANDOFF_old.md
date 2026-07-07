# AlphaEvolve & FunSearch 발표자료 — 인수인계 문서

> 다른 사람이 이어받아 작업할 수 있도록 정리한 종합 문서.
> `main.tex` / `main.pdf`와 같은 디렉토리에 위치.

---

## 1. 한눈에 보기

| 항목 | 내용 |
|---|---|
| **제목** | AlphaEvolve and FunSearch: Discovering Mathematics with LLMs |
| **분량** | 50분 발표 (overlay 포함 149-page PDF, 약 35 frames + section TOC + 표지/감사) |
| **대상** | 중·고등학교 수학 교사 + 수학교육 대학원생 |
| **언어** | 슬라이드는 영어, 발표는 발표자 재량 (한국어 강연 가정) |
| **현재 상태** | 골격 완성, 컴파일 정상 (overfull box 0개), 표지 placeholder만 채우면 즉시 사용 가능 |

---

## 2. 파일 구조

```
Evolve-type-agent-research/
├── presentation/
│   ├── main.tex              ← 발표 슬라이드 (편집 대상)
│   ├── main.pdf              ← 컴파일 결과
│   ├── HANDOFF.md            ← 이 문서
│   └── figures/              ← (현재 비어있음, 신규 그림 추가 위치)
├── references/
│   ├── AI-for-Math.tex       ← 스타일 참고용 (KIAS CAINS Welcome Talk, April 2026)
│   ├── Presentation1.tex     ← 스타일 참고용 (FunSearch Winter School)
│   ├── Meeting1.tex          ← 스타일 참고용 (FunSearch KIAS Winter School)
│   └── figures/              ← 17개 이미지 (main.tex에서 \graphicspath로 연결)
└── sources/
    ├── INDEX.md              ← 21개 PDF 카탈로그
    └── 01-21 PDFs            ← 카테고리: Core / Novel Math / Successors / Sister / AlphaTensor(제외)
```

`main.tex`의 `\graphicspath{{./figures/}{../references/figures/}}` 설정으로 두 폴더에서 이미지를 찾습니다.

---

## 3. 컴파일 방법

```bash
cd presentation
pdflatex main.tex   # 1회차: 본문 컴파일
pdflatex main.tex   # 2회차: cross-references 해결
```

특수 패키지 의존성: TeX Live 2026 (또는 `amsmath`, `tikz`, `tikz-cd`, `ytableau`, `booktabs`, `enumitem`, `bbm` 등이 포함된 배포판).

---

## 4. 발표의 핵심 컨셉

### 4.1 발표가 던지는 메시지

이 발표는 단순히 AI 도구 소개가 아니라, **"AI가 새로운 수학을 발견하고 있다"** 는 사실을 청중(수학교사)에게 전달하는 것이 목표.

순서대로 다음 메시지를 전달:
1. **Hook** — Strassen이 1969년에 7번 곱셈을 발견한 후 56년간 4×4 행렬에서 49가 깨지지 않았다.
2. **본론** — AlphaEvolve가 48번을 찾았다. 어떻게?
3. **클라이맥스** — Williamson의 Bruhat hypercube 결과: AI가 패턴을 제안하고, 수학자가 정리를 증명했다.
4. **메시지** — *"AI generated the pattern. The mathematicians proved the theorem."*

### 4.2 핵심 punchline (반복되는 슬로건)

발표 전체에 다음 문장들이 반복적으로 등장. 이들은 이 발표의 정신:

- **"Don't trust the LLM. Trust an evaluator."**
- **"The mathematical guarantee comes from the evaluator, not the LLM."**
- **"AI suggested the pattern. The mathematicians proved the theorem."**
- **"Pure mathematics and industrial impact, from one system."**
- **"A tool a graduate student can run on a laptop, today."**
- **"AlphaEvolve does not replace mathematicians. It is a new collaborator in the loop."**

이 punchline들은 발표 중 절대 단순화·삭제하면 안 됨. 발표의 정체성.

---

## 5. 의도적으로 제외/포함된 것들

### 5.1 ❌ 제외된 것 (사용자 명시적 결정)

| 제외 대상 | 이유 |
|---|---|
| **AlphaTensor** | 발표 범위에서 빠지기로 결정. RL 기반이라 이 발표의 "LLM × GA" 패러다임과 다름. |
| **FunSearch vs. AlphaEvolve 비교 슬라이드** | 이 발표는 두 시스템을 *별로 구분하지 않음*. FunSearch에서 AlphaEvolve로의 발전 자체가 초점이 아니다. |
| **Genetic algorithm 2-min 영상 단독 슬라이드** | 영상 링크만 GA 슬라이드 끝에 한 줄로 남김. |
| **"Two-minute primer"/"×1.5 speed" 라벨** | YouTube 링크는 bare URL만 표시. |

### 5.2 ✅ 의도적으로 포함된 것

| 포함 | 이유 |
|---|---|
| **Strassen 56-year mystery (Hook)** | 발표 전체를 관통하는 미스터리. Hook → matrix multiplication 예제에서 회수. |
| **Ramsey numbers 예제** | 수학 백그라운드가 약한 청중에게도 설명하기 쉬움. 청중 맞춤 결정. |
| **4가지 예제 순서: cap set → Ramsey → matmul → Bruhat** | 단순한 것부터 복잡한 것 순. matmul에서 Strassen Hook 회수. Bruhat가 클라이맥스. |
| **Bruhat hypercubes (Williamson 결과)** | 이 발표의 클라이맥스. "AI가 정리를 *제안*하고 수학자가 *증명*"의 가장 명확한 사례. |
| **Try it yourself + Education** | 청중이 교사이므로 "내가/내 학생이 어떻게 할 수 있는가"가 중요. |

---

## 6. 발표 구조 (6 sections + Hook)

### Hook (4 frames, 섹션 없음)
1. **A puzzle to start with** — 2×2 행렬 8 multiplications
2. **Strassen's surprising answer** — Strassen의 7-multiplication 알고리즘 전체 식
3. **What about 4×4 matrices?** — 재귀: 7×7 = 49
4. **A 56-year mystery** — 1969–2024 49 깨지지 않음 → AlphaEvolve가 48 발견

### §1. AI for mathematics (2 frames)
- **Three flavors of "AI for mathematics"** — Pattern recognizer / **Code agent** / Theorem prover 비교 표. 가운데 열(Code agent)이 이 발표의 초점.
- **The lineage of code agents** — FunSearch (Nature 2023) → AlphaEvolve (DeepMind 2025) → Williamson, Tao, ... (2025–2026).

### §2. From genetic algorithms to AlphaEvolve (5 frames)
- **Borrowing from evolution** — GA 4단계 + YouTube 링크 (`youtu.be/Yr_nRnqeDp0`, ×1.5 권장)
- **Where classical GAs struggle** — code 같은 candidate에는 random mutation이 무력
- **LLMs as a smart mutation operator** — KeyIdea 박스: random mutation 대신 LLM이 코드 재작성
- **But LLMs hallucinate ...** — "Don't trust the LLM. Trust an evaluator."
- **The role of the evaluator** — KeyIdea 박스: LLM이 코드 작성, 평가자가 결정적으로 검증
- **One sentence summary** — 박스 안: AlphaEvolve = LLM(mutation) + Evaluator(selection) + Evolution loop

### §3. Inside AlphaEvolve (4 frames)
- **The FunSearch / AlphaEvolve loop** — `Workflow.png` 그림 (from Ellenberg et al. 2025)
- **Four components** — Program database / Prompt sampler / LLM ensemble (Gemini Flash + Pro) / Evaluator pool
- **One iteration, in pseudocode** — 6단계 + "Repeat 10⁴–10⁶ times"
- **What is *actually* being evolved?** — "Not the mathematical object, but the *program* that constructs it." 3가지 예제 미리보기.

### §4. Discoveries (12 frames)
**§4a. Cap Set (3 frames)**
- **Example 1: the Cap Set problem** — 정의 + dim 8 record 496 (~20년 정체)
- **Example 1: the Cap Set problem (image)** — `FunSearch_Eval_Solve.png`. FunSearch가 512 발견, 첫 record 갱신.
- **Example 1: the priority function** — verbatim Python `priority` 함수, FunSearch가 evolve하는 출발점.

**§4b. Ramsey (3 frames)**
- **Example 2: Ramsey numbers** — Party problem + 일반 정의 + 표 (R(3,3)=6 부터 R(5,5)∈[43,48])
- **Example 2: the small-Ramsey table** — `r44-14.png` (R(4,4) > 14 witness)
- **Example 2: AlphaEvolve takes a single shot** — Nagda et al. 표. R(3,13), R(4,13), …, R(4,20)에서 9개 lower bound 갱신.

**§4c. Matrix multiplication (3 frames) — Hook 회수**
- **Example 3: remember the 49?** — Hook과 연결. AlphaEvolve가 48 발견 (May 2025).
- **Example 3: how was it found?** — Generic gradient solver의 *코드*가 evolve. Trick: 복소 계수.
- **Example 3: real-world impact** — Google 인프라 적용. Matmul kernel 23% 빠름, scheduler 0.7% 회수, FlashAttention 32% 단축.

**§4d. Bruhat hypercubes (3 frames) — 클라이맥스**
- **Example 4: hypercubes inside Bruhat order** — `hypercube.png` 그림. Bruhat order 정의. Goal: large boolean intervals.
- **Example 4: the AlphaEvolve experiment** — Williamson et al. (2026)이 AlphaEvolve에 질문. 답은 *dyadically well-distributed permutations* (Monte Carlo / 수리금융에서 온 개념).
- **Example 4: a theorem from the loop** — `WilliamsonResult` 정리: $S_{2^m}$의 dyadically well-distributed permutations이 차원 $m \cdot 2^{m-1}$의 boolean interval. **"AI suggested the pattern. The mathematicians proved the theorem."**

### §5. Honest assessment (2 frames)
- **What AlphaEvolve cannot (yet) do** — No proofs / Needs evaluator / Bijections 어려움 / Compute cost
- **The honest message** — "Not a replacement, but a collaborator." Williamson 사례가 prototype.

### §6. Try it yourself (5 frames — 교육 implications 포함)
- **An accessible toolkit** — Ellenberg et al. (arXiv:2503.11061): 노트북에서 돌아가는 FunSearch 구현
- **Two starter problems** — (1) R(4,4) ≥ 18 재발견, (2) no-isosceles subset of n×n grid
- **Designing your own problem** — 3가지 조건 (Python로 표현 가능 / 결정적 evaluator / 의미있는 baseline-SOTA gap)
- **What should we teach our students?** — Mathematical literacy / Programming as scratch paper / Verification, not authority
- **Three takeaways** — (1) AI가 새 수학을 *discover* / (2) 신뢰는 evaluator에서 / (3) The model is *collaboration*

### 마무리
- **References (key papers)** — 6개 논문 (FunSearch, AlphaEvolve, Ellenberg et al., Tao/Wagner/Gómez-Serrano, Williamson, Nagda)
- **Thank you!**

---

## 7. 스타일 결정사항

### 7.1 LaTeX 환경 / 사용자 정의

```latex
\usetheme{CambridgeUS}

% 색강조
\newcommand\remph[1]{\emph{\textcolor{red}{#1}}}     % 빨간 italic
\newcommand\bemph[1]{\emph{\textcolor{blue}{#1}}}    % 파란 italic

% 명명된 정리 박스
\newtheorem*{Strassen}{Strassen (1969)}
\newtheorem*{AlphaEvolveResult}{AlphaEvolve (2025)}
\newtheorem*{WilliamsonResult}{Ellenberg--Libedinsky--Plaza--Simental--Williamson (2026)}
\newtheorem*{KeyIdea}{Key idea}
\newtheorem*{OpenProblem}{Open problem}

% 섹션 시작 시 자동으로 TOC 슬라이드
\AtBeginSection[]{...}
```

### 7.2 색강조 사용 규칙

- `\bemph{}` (파란 italic): 개념·시스템 이름. 예: *FunSearch*, *AlphaEvolve*, *Bruhat order*.
- `\remph{}` (빨간 italic): 핵심 수치·결과. 예: *7 multiplications*, *48 multiplications*, *512*.
- 일반 `\emph{}`: 본문 내 강조 (italic, 색 없음).

`\remph`는 수학 모드(`\[…\]`) 안에서 사용하면 에러. 수학 모드에서는 `\textcolor{red}{}` 직접 사용.

### 7.3 표현 스타일 — 매우 중요

발표자가 **"keyword 위주, prose 최소화"** 를 명시적으로 요청. 슬라이드는 발표자가 입으로 설명할 keyword만 나열. 다음 패턴을 적용:

| Before (피해야 할 패턴) | After (선호 패턴) |
|---|---|
| "X is Y that does Z" | "X — Y, Z" |
| "Anyone who has X knows..." | "X — as anyone who has tried Y knows" |
| "There is an algorithm..." | (drop) |
| "It was discovered by..." | "Found by..." |
| "Author1, Author2, ..., and AuthorN (2026, arXiv:...)" | "Author1 et al.\ (arXiv:...)" |
| "To attack a new problem, modify..." | "New problem: modify..." |
| "AlphaEvolve was given a..." | "Input: a..." |

**과도하게 축약하지 말 것.** "기존 prose의 살을 빼고 뼈만 남기되, 단어 자체를 축약(예: matmul, HPC)하는 것은 신중히". 청중이 수학 교사임을 고려.

### 7.4 그림 사용 가이드

이미지 스케일링은 `scale=` 보다 `height=` / `width=`를 우선. `scale=`은 자연 크기에 의존해서 frame overflow를 일으키기 쉬움. 현재 사용 중:

- `\includegraphics[width=.85\textwidth]{Workflow.png}` — Inside AlphaEvolve loop
- `\includegraphics[height=5cm]{FunSearch_Eval_Solve.png}` — Cap Set image
- `\includegraphics[height=4cm]{r44-14.png}` — R(4,4)>14 witness
- `\includegraphics[height=3.2cm]{hypercube.png}` — Bruhat hypercube (⚠ 5.4 참조)

### 7.5 사용 중인 figures

| 파일 | 위치 | 용도 |
|---|---|---|
| `Workflow.png` | `references/figures/` | Inside AlphaEvolve loop 슬라이드 |
| `FunSearch_Eval_Solve.png` | `references/figures/` | Cap Set 시각화 |
| `r44-14.png` | `references/figures/` | R(4,4) > 14 witness coloring |
| `hypercube.png` | `references/figures/` | Bruhat hypercube (⚠ 주의) |

⚠ **`hypercube.png` 주의**: 이 그림은 KIAS *AI-for-Math.tex* 발표용으로 만들어진 *Kazhdan–Lusztig hypercube decomposition* 그림. 모양은 같지만 맥락이 다소 다름. 가능하면 caption 추가하거나 더 적절한 그림으로 대체 고려.

---

## 8. 다음 사람이 해야 할 일

### 8.1 즉시 채워야 할 placeholder

`main.tex` 54–57 라인:
```latex
\title[AlphaEvolve \& FunSearch]{AlphaEvolve and FunSearch:\\ Discovering Mathematics with LLMs}
\author[Speaker]{[Speaker Name]}              ← 여기
\institute[Institution]{[Institution]}        ← 여기
\date[]{[Venue / Event] \\ {[Date]}}          ← 여기, 여기
```

### 8.2 발표 전 검증 권장

- **수치 정확성**:
  - Cap set dim 8 = 512 (확정)
  - Ramsey R(5,5) ∈ [43, 48] (현재 표시값, 보수적)
  - R(4,6) ∈ [35, 40] (보충 표기, 강의 전 한 번 확인 권장)
  - AlphaEvolve의 9개 Ramsey 갱신 표 (Nagda et al. arXiv:2603.09172)
  - 4×4 matmul: 49 → 48 (May 2025)
- **YouTube 링크 확인**: `youtu.be/Yr_nRnqeDp0` (3분 영상, ×1.5 재생 권장)
- **arXiv ID 확인**:
  - 2506.13131 (AlphaEvolve)
  - 2503.11061 (Ellenberg toolkit)
  - 2511.02864 (Tao, Wagner, ...)
  - 2601.01235 (Williamson Bruhat)
  - 2603.09172 (Nagda Ramsey)
  - 2511.20987 (bijection limitation 언급)

### 8.3 강연장 점검 사항

- **Strassen 7-mult 슬라이드** (Strassen's surprising answer): $M_1$–$M_7$ 7개 식 + $c_{ij}$ 4개 식이 한 화면에. `\pause`로 두 단계 노출. 강연장 화면에서 글자 크기 한 번 확인.
- **Three flavors 표**: `\arraystretch{1.1}` + `\resizebox{\textwidth}` 으로 빠듯하게 fit. 다른 환경에서 다시 컴파일 시 주의.
- **Bruhat hypercube 그림**: 7.5 참조. 맥락 caption 추가 고려.

### 8.4 분량 체크 (50분 가정)

149 page (overlay 포함), 약 35 frames + section TOC + 표지/감사 = **약 45 슬라이드 단위**.
50분 / 45 ≈ 67초/슬라이드. 빠듯한 편. 첫 시연 후 시간이 모자라면:
- **압축 가능 후보**: §3 *Inside AlphaEvolve*의 4 frames → 3 frames (Four components와 Pseudocode를 합치기)
- **압축 가능 후보**: §6 *Try it yourself*의 5 frames → 4 frames (Designing your own problem 흡수)
- **건드리지 말 것**: Hook 4 frames, §4 *Discoveries* 12 frames (메인 콘텐츠), §5 *Honest assessment* 2 frames.

---

## 9. 대화 이력 요약

이 인수인계 이전까지의 작업 흐름:

### Phase 1: 자료 수집
- `sources/`에 21개 PDF 수집 + INDEX.md 카탈로그.
- 카테고리: Core / Novel Mathematical Research / Successor Frameworks / Sister Techniques / AlphaTensor (제외).
- AlphaTensor PDF 2개 다운로드 시도 후 발표에서 제외 결정.
- Williamson Bruhat 논문 식별 (arXiv:2601.01235).
- Nagda Ramsey 논문 식별 (arXiv:2603.09172).
- "단순 최적화 개선"이 아닌 "novel forms of mathematical research" 사례 우선 식별.

### Phase 2: 발표 골격 결정
- 청중: 중·고등학교 수학 교사 + 수학교육 대학원생.
- 분량: 50분.
- 동기부여 문제: Strassen 미스터리 (사용자 선택).
- 예제 4개 + 순서: cap set → Ramsey → matmul → Bruhat (사용자 선택; Ramsey가 비전공자에게 친근).
- AlphaTensor 제외 명시.

### Phase 3: 스타일 매칭
- `references/`의 3개 .tex 파일 (`AI-for-Math.tex`, `Presentation1.tex`, `Meeting1.tex`) 분석.
- CambridgeUS theme, `\bemph`/`\remph` 색강조, 명명 theorem 환경 등 스타일 채택.
- 표지는 placeholder, 영상은 링크만, 영상 단독 슬라이드 없음 등 결정.

### Phase 4: 초안 작성 (41 frames, 8 sections)
- `main.tex` 작성 → 컴파일 (`\\ [Date]` 파싱 에러, math mode `\remph` 에러 수정 후 154 page PDF).

### Phase 5: 6가지 수정 (대화 시작 직후)
1. GA 영상 단독 슬라이드 → GA 슬라이드 끝에 링크만
2. GPT-4 → GPT-5
3. "One sentence summary" 박스 페이지 초과 수정 (`\begin{aligned}`로 두 줄 분할)
4. "FunSearch vs. AlphaEvolve" 비교 슬라이드 삭제 (이 발표는 둘을 구분 안 함)
5. Williamson만 emphasis된 어색한 표기 수정 → "Williamson et al."
6. Section 8개 → 6개로 축소 (§2+§3 합침: "From genetic algorithms to AlphaEvolve"; §7+§8 합침: "Try it yourself"에 교육 implications 흡수)

### Phase 6: 링크 단순화 + 전반 prose 단순화
- "Two-minute primer / ×1.5 speed" 라벨 제거 → bare URL만.
- 25곳 이상에서 prose → keyword/phrase 변환.
- 수식·정리 박스·문제 정의·코드 블록·핵심 punchline은 보존.

### Phase 7: Frame overflow 검증
- 3개 frame에서 overfull 발견:
  - **Three flavors of AI for math**: arraystretch 1.4 → 1.1, vspace 제거
  - **Cap Set 이미지 슬라이드**: `scale=.4` → `height=5cm`
  - **Small-Ramsey table**: `scale=.3` → `height=4cm`, vspace 제거
- 최종: overfull box 0개, 149 page.

---

## 10. 발표자가 명시한 선호·금기

대화에서 발표자가 명시했거나 행동으로 드러난 원칙들:

| 원칙 | 메모 |
|---|---|
| **AlphaTensor는 발표에 불필요** | "아냐 AlphaTensor까지는 발표에 필요없겠다." |
| **FunSearch와 AlphaEvolve를 별로 구분하지 않음** | "이 발표에서는 FunSearch와 AlphaEvolve를 별로 구분하지 않을꺼야." |
| **표지는 발표자가 직접 채움** | placeholder 그대로 둘 것. |
| **링크는 bare URL** | 라벨/주석 없이 깔끔하게. |
| **prose 최소화, keyword 위주** | "핵심 키워드들만 나열해도 내가 말로 설명할 수 있어." |
| **너무 축약하지 말 것** | "너무 축약할 필요는 없지만 조금 단순화해줘." |
| **단일 저자 강조 어색** | 5인 공저 중 한 명만 emphasize는 어색. "Author et al." 선호. |
| **Section 너무 많으면 부담** | 8개 → 6개로 축소. |
| **Strassen이 motivation 문제** | Hook → matmul example의 회수 구조를 유지. |
| **Ramsey는 비전공자 친화적이라 포함** | 4가지 예제 중 두 번째 자리. |

---

## 11. 자주 쓰일 명령

```bash
# 컴파일 (cross-references 위해 2회)
cd /Users/bhwang/Projects-local/Evolve-type-agent-research/presentation
pdflatex main.tex && pdflatex main.tex

# Overflow 체크
grep -n "Overfull" main.log

# Frame title 목록 (구조 파악)
grep -n "frametitle" main.tex

# Section 목록
grep -n "^\\\\section" main.tex
```

---

## 12. 참고: 참조한 외부 자료

### 사용한 논문 (References 슬라이드에 등재)

1. **FunSearch** — Romera-Paredes et al., *Mathematical discoveries from program search with large language models*, Nature 625 (2024) 468–475.
2. **AlphaEvolve** — Novikov et al., *AlphaEvolve: A coding agent for scientific and algorithmic discovery*, arXiv:2506.13131 (2025).
3. **Toolkit** — Ellenberg, Fraser-Taliente, Harvey, Srivastava, Sutherland, *Generative modeling for mathematical discovery*, arXiv:2503.11061 (2025).
4. **Tao 등** — Georgiev, Gómez-Serrano, Tao, Wagner, *Mathematical exploration and discovery at scale*, arXiv:2511.02864 (2025).
5. **Williamson Bruhat** — Ellenberg, Libedinsky, Plaza, Simental, Williamson, *Bruhat intervals that are large hypercubes*, arXiv:2601.01235 (2026).
6. **Ramsey AlphaEvolve** — Nagda, Raghavan, Thakurta, *Reinforced generation of combinatorial structures: Ramsey numbers*, arXiv:2603.09172 (2026).

### 본문에 언급된 추가 자료

- **arXiv:2511.20987** — bijection 한계 언급 (limitations 슬라이드)
- **YouTube `youtu.be/Yr_nRnqeDp0`** — 3-minute genetic algorithm primer

### sources/INDEX.md

`../sources/INDEX.md`에 21개 PDF 카탈로그가 정리되어 있음. 발표에 참고했지만 인용하지 않은 자료들도 포함.

---

## 13. 끝맺음

이 발표의 정신은 한 줄로:

> **"AI가 수학적 패턴을 제안하고, 인간 수학자가 정리를 증명한다."**

수정·확장 시 이 정신에 맞는지 확인하는 것이 가장 좋은 점검 기준.

좋은 발표 되시기를.

---

*Generated as a handoff document for the AlphaEvolve & FunSearch presentation. 모든 결정 사항과 컨텍스트는 이 문서에 통합됨. 추가 질문이나 수정 시에는 main.tex와 이 문서를 함께 업데이트할 것.*
