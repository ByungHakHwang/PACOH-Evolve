# Sources — AlphaEvolve & 관련 Research Tool 조사

이 디렉토리는 AlphaEvolve 류 evolutionary coding-agent / LLM 기반 algorithm-discovery 연구에 대한
원전 논문과 관련 자료를 모아둔 것입니다. 발표자료 작성을 위한 1차 reference입니다.

각 파일명은 `NN_제목_연도_식별자.pdf` 형식입니다.

> **발표 초점 (2026-05 결정)**: AlphaTensor 라인은 발표에서 제외, **AlphaEvolve / FunSearch로 이뤄진 새로운 형태의 수학 연구**(structure / Ramsey / complexity / 정리 발견)에 집중.

---

## 1. 핵심 (Core) — AlphaEvolve & FunSearch

| # | 파일 | 저자 / 연도 | 한 줄 요약 |
|---|------|-------------|----------|
| 01 | `01_AlphaEvolve_2025_DeepMind_whitepaper.pdf` | DeepMind, 2025-05 | AlphaEvolve 공식 white paper. Gemini 기반 evolutionary coding agent. **본 발표의 메인 텍스트.** |
| 02 | `02_AlphaEvolve_2025_arxiv_2506.13131.pdf` | DeepMind, 2025-06 | 위 white paper의 arXiv 버전 (`arXiv:2506.13131`). 인용용 ID. |
| 03 | `03_FunSearch_2023_Nature.pdf` | Romera-Paredes et al., Nature 2023-12 | **첫 LLM-evolutionary 수학 발견** (cap set, online bin-packing). AlphaEvolve의 직계 조상. |

---

## 2. 새로운 형태의 수학 연구 (Novel Mathematical Research) ⭐

> 단순한 "더 좋은 숫자 찾기"(optimization)를 넘어 **구조 정리 / 분류 / 일반 공식 / 형식적 증명까지 도달한** 사례들. 발표의 클라이맥스.

| # | 파일 | 저자 / 연도 | 한 줄 요약 |
|---|------|-------------|----------|
| 16 | `16_Williamson_Bruhat_Hypercubes_2026_arxiv_2601.01235.pdf` | **Ellenberg, Libedinsky, Plaza, Simental, Williamson** — 2026-01 | **Bruhat order 안의 큰 hypercube 구간 발견.** AlphaEvolve가 작은 n에 대해 잘 작동하는 permutation 패턴을 제시 → 저자들이 일반 n으로 증명. **dyadically well-distributed permutations**가 정확히 그 구간을 이룸을 증명. *Representation theory / Coxeter combinatorics 영역*. |
| 17 | `17_Ramsey_Numbers_AlphaEvolve_2026_arxiv_2603.09172.pdf` | Nagda, Raghavan, Thakurta (Berkeley + Google DeepMind) — 2026-03 | **9개의 고전 Ramsey number lower bound 갱신** (R(3,13): 60→61, R(4,16): 170→**174**, R(4,20): 234→237 등). AlphaEvolve를 *meta-search*로 사용 — 알고리즘 자체를 진화시켜 그래프 구성 알고리즘을 만듦. |
| 18 | `18_Hardness_of_Approximation_AlphaEvolve_2025_arxiv_2509.18057.pdf` | Nagda, Raghavan, Thakurta — 2025-09 | "Reinforced Generation of Combinatorial Structures: 시리즈"의 **complexity-theory 편**. **MAX-4-CUT 0.987**, **MAX-3-CUT 0.9649** NP-hardness 새 inapproximability 결과 (gadget reduction을 AlphaEvolve로 발견). 163-vertex 거의-extremal Ramanujan graphs 발견. |
| 04 | `04_AlphaEvolve_Math_at_Scale_2025_arxiv_2511.02864.pdf` | Georgiev, Gómez-Serrano, **Terence Tao**, Wagner — 2025-11 | 67개 수학 문제에 AlphaEvolve 적용. **finite field Kakeya 문제는 AlphaEvolve(발견) → Gemini Deep Think(증명) → AlphaProof(Lean에서 형식 검증)** 풀파이프라인 시연. 일부 문제는 finite case → 일반 공식 generalization까지 함. |
| 19 | `19_FunSearch_for_Mathematicians_Ellenberg_2025_arxiv_2503.11061.pdf` | Ellenberg, Fraser-Taliente, Harvey, Srivastava, Sutherland — 2025-03 | **수학자가 직접 쓸 수 있는 FunSearch 재구현** (PR/HPC 불필요). Cap-set, **narrow-admissible-tuple** (number theory!), **no-isosceles** 문제에 적용. *작업 수학자용 도구*라는 새 패러다임. |
| 20 | `20_MultiAgent_Math_Concepts_2026_arxiv_2603.04528.pdf` | Aggarwal, Kim, Ek, Mishra (Cambridge) — 2026-03 | 수학적 *개념(concept)* 발견을 다중-에이전트 시스템으로 시도. Euler 다면체 conjecture에서 영감, **homology 개념을 polyhedral data + 선형대수만으로 자율적 재발견**. 추측-증명-반례 사이클을 모델링. |

### 발표용 short blurb (각 결과의 "왜 새로운가")

- **Williamson (Bruhat hypercubes)**: 단순한 lower bound가 아니라 **정확한 분류 정리**. AI가 패턴을 보여주고 사람이 정리로 만든 첫 representation theory 사례 중 하나.
- **Ramsey**: 1세기 가까이 *bespoke* 한 명령형 알고리즘으로 한 칸씩 갱신해 온 표를 **하나의 meta-알고리즘**으로 9칸 갱신.
- **Hardness of Approximation**: 단순한 construction 발견이 아니라 **NP-hardness 증명에 들어가는 gadget reduction** 자체를 AI가 설계.
- **Tao et al. + finite field Kakeya**: AI가 *발견 → 증명 → 형식화(Lean)* 까지의 **완전 자동 파이프라인**을 처음 시연.
- **Ellenberg et al.**: AI를 일반 수학자에게 보급 (도구의 democratization). number theory에 적용된 첫 본격 사례.
- **Multi-agent concepts**: bound 갱신이 아니라 **수학적 개념 자체의 자동 emergence**. 가장 근본적 도전.

---

## 3. 후속·경쟁 시스템 (Competing & Successor Frameworks)

| # | 파일 | 저자 / 연도 | 한 줄 요약 |
|---|------|-------------|----------|
| 07 | `07_CodeEvolve_2025_arxiv_2510.14150.pdf` | 2025-10 | AlphaEvolve를 island-based GA + 모듈러 LLM orchestration으로 재현한 오픈소스. |
| 12 | `12_OpenEvolve_Bijection_2025_arxiv_2511.20987.pdf` | 2025-11 | OpenEvolve로 Dyck path 등 **bijection 발견**을 시도. "AI도 어렵다"의 negative-ish report. |
| 13 | `13_ThetaEvolve_2025_arxiv_2511.23473.pdf` | 2025-11 | "Test-time learning on open problems" — open problem에서 evolution의 한계. |
| 14 | `14_Scientific_Algorithm_Discovery_DeepResearch_2025_arxiv_2510.06056.pdf` | 2025-10 | AlphaEvolve에 deep-research / 문헌검색을 결합. |
| 21 | `21_FlowBoost_Extremal_Discovery_2026_arxiv_2601.18005.pdf` | Bérczi, Hashemi, Klüver — 2026-01 | **AlphaEvolve의 직접 경쟁자**. LLM 대신 conditional flow matching + reward-guided fine-tuning. circle packing에서 AlphaEvolve를 능가 (적은 자원으로). |

OpenEvolve (Sharma, GitHub: `algorithmicsuperintelligence/openevolve`) 자체는 별도 arXiv 논문 없이 구현체로만 공개됨.

---

## 4. 자매 기법 (Sister Techniques) — LLM × Evolution

| # | 파일 | 저자 / 연도 | 한 줄 요약 |
|---|------|-------------|----------|
| 08 | `08_Algorithm_Discovery_Evo+RL_2025_arxiv_2504.05108.pdf` | 2025-04 | LLM evolutionary search + **RL fine-tuning of the search operator (LLM)**. AlphaEvolve의 "다음 단계" 후보. |
| 09 | `09_Eureka_2023_arxiv_2310.12931.pdf` | NVIDIA, ICLR 2024 | LLM이 RL **reward function 코드**를 진화적으로 설계. 29개 환경 중 83% 인간 전문가 능가. |
| 10 | `10_EvoPrompt_2023_arxiv_2309.08532.pdf` | Microsoft, ICLR 2024 | 코드 대신 **prompt**를 evolutionary algorithm으로 최적화. 같은 패러다임의 prompt-level 버전. |
| 11 | `11_Promptbreeder_2023_arxiv_2309.16797.pdf` | DeepMind, 2023-09 | self-referential prompt evolution. |

---

## 5. 참고용 — AlphaTensor 라인 (발표에서 제외)

> 발표에는 포함하지 않기로 결정 (2026-05). RL 기반 단일 문제 시스템이라 본 발표의 "LLM-evolutionary" 주제와 결이 다름.

| # | 파일 | 비고 |
|---|------|------|
| 05 | `05_AlphaTensor_2022_Nature.pdf` | Fawzi et al., Nature 2022. AlphaZero 기반 RL로 텐서 분해. |
| 06 | `06_4x4_MatMul_48mults_2025_arxiv_2506.13242.pdf` | AlphaEvolve의 4×4 matmul 결과를 ℚ로 환원한 학계 follow-up. |
| 15 | `15_OpenTensor_2024_arxiv_2405.20748.pdf` | AlphaTensor 오픈 reproduction. |

---

## 코드 / 외부 리소스

- AlphaEvolve 공식 결과: <https://github.com/google-deepmind/alphaevolve_results>
- AlphaEvolve repository of math problems: <https://github.com/google-deepmind/alphaevolve_repository_of_problems>
- FunSearch 공식 코드: <https://github.com/google-deepmind/funsearch>
- OpenEvolve (community impl): <https://github.com/algorithmicsuperintelligence/openevolve>
- Ramsey 결과 그래프 + 알고리즘 GitHub (논문 #17 부록): 논문 내 링크 참조
- Tao 블로그 — Mathematical exploration at scale: <https://terrytao.wordpress.com/2025/11/05/mathematical-exploration-and-discovery-at-scale/>
- DeepMind 블로그 — AlphaEvolve: <https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/>
- DeepMind 블로그 — FunSearch: <https://deepmind.google/blog/funsearch-making-new-discoveries-in-mathematical-sciences-using-large-language-models/>

---

## 발표 흐름 (제안 v2 — 수학 발견 중심)

1. **문제 설정**: AI가 수학적 *발견*을 할 수 있는가? optimization을 넘어 *정리·구조·개념*까지?
2. **방법론**: AlphaEvolve / FunSearch의 evolutionary code-search 메커니즘. (사상의 핵심: LLM은 mutation operator, evaluator가 검증.)
3. **수학적 발견 4단계 사다리** (발표 클라이맥스):
   1. **Optimization** (lower / upper bound 갱신) — Ramsey numbers (#17), kissing number (#01), Erdős minimum overlap.
   2. **Structure / 분류 정리** — Williamson Bruhat hypercubes (#16), dyadically well-distributed permutations 정리.
   3. **Complexity / 메타-수학** — gadget reduction 발견으로 NP-hardness 갱신 (#18).
   4. **발견 → 증명 → 형식화** — Tao et al의 finite-field Kakeya 풀파이프라인 (#04).
   5. **개념의 자율적 emergence** — Cambridge multi-agent (#20), bound조차 아닌 *concept* 자체.
4. **수학자에게의 의미**: Ellenberg group의 도구 democratization (#19) + Williamson의 협업 모델.
5. **한계와 경쟁**: Bijection의 어려움 (#12), FlowBoost의 자원 효율성 (#21).
6. **앞으로**: 형식 증명과의 결합, RL 통합 (#08), open problem.
