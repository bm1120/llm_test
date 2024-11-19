# llm_test
AI 도구 분석 및 Notion 데이터베이스 자동화 프로젝트

## 프로젝트 개요
Perplexity AI API를 활용하여 최신 AI 도구들을 분석하고, 그 결과를 Notion 데이터베이스에 자동으로 저장하는 프로그램입니다.

## 설정 방법

1. 프로젝트 디렉토리 설정:
   - 프로젝트 루트에 `debug_output` 디렉토리 생성:
   ```bash
   mkdir debug_output
   ```
   - 로그 파일이 이 디렉토리에 저장됩니다
   - 이미 .gitignore에 포함되어 있어 로그 파일은 git에 추적되지 않습니다

2. `.env.local` 파일을 프로젝트 루트에 생성하고 다음 환경 변수를 설정하세요:
    ```bash
    NOTION_TOKEN=your_notion_integration_token
    NOTION_DATABASE_ID=your_notion_database_id
    PERPLEXITY_API_KEY=your_perplexity_api_key
    ```

3. Notion 설정:
   - Notion 통합(Integration) 생성 및 토큰 발급
     1. https://www.notion.so/my-integrations 접속
     2. 'New integration' 클릭
     3. 통합 이름 설정 및 생성
     4. 생성된 'Internal Integration Token' 복사하여 `NOTION_TOKEN`에 설정
   
   - 데이터베이스 생성 및 속성 설정:
     1. Notion에서 새 데이터베이스 생성
     2. 다음 속성 추가:
        - Name (제목)
        - Link (URL)
   
   - 데이터베이스 ID 확인:
     1. 데이터베이스 페이지를 웹에서 열기
     2. URL 확인: `https://www.notion.so/{workspace_name}/{database_id}?v={view_id}`
     3. URL에서 workspace_name 다음에 오는 32자리 문자열이 데이터베이스 ID
     4. 복사한 ID를 `NOTION_DATABASE_ID`에 설정
   
   - 통합 연결:
     1. 데이터베이스 페이지에서 우측 상단 ... 메뉴 클릭
     2. 'Connections' 선택
     3. 생성한 통합 검색 후 추가

4. Perplexity AI API 키 발급:
   - https://www.perplexity.ai/settings/api 에서 API 키를 발급받으세요.

## 실행 방법

1. Docker Compose로 실행:
   ```bash
   docker-compose up --build
   ```

2. 로그 확인:
   - 실행 중 로그는 콘솔에서 실시간으로 확인 가능
   - 상세 로그는 `debug_output/ai_tools_crawler.log` 파일에서 확인

## 주요 기능
- 최신 AI 도구 목록 자동 수집
- 각 도구별 상세 분석 수행
- Notion 데이터베이스에 분석 결과 자동 저장
- 중복 도구 검사 및 제외
- 참조 번호, 주석 등 자동 정제

## 기술 스택
- Python 3.9
- Docker & Docker Compose
- Perplexity AI API
- Notion API

## 참고사항
- API 요금 절약을 위해 테스트 시에는 'llama-3.1-8b-instruct' 모델 사용 가능
- 실제 운영 시에는 'llama-3.1-sonar-small-128k-online' 모델 권장
- 두 모델의 출력 결과와 포맷이 다소 차이가 있기 때문에 추가 정제 작업 필요

## GCP 배포 방법

### 1. Cloud Functions 설정
1. GCP 콘솔 → Cloud Functions 접속
2. "함수 만들기" 클릭
3. 기본 설정:
   - 함수 이름: `ai-tool-analyzer`
   - 리전: `asia-northeast3`
   - 트리거 유형: `HTTP`
   - 인증: `인증이 필요함`
4. 런타임 설정:
   - 런타임: Python 3.9
   - 진입점: `analyze_tools`
   - 메모리: 256MB
   - 타임아웃: 540초
5. 소스 코드:
   - `main.py` 파일 생성 (기존 코드 참조)
   ```python:main.py
   startLine: 1
   endLine: 419
   ```
   - `requirements.txt` 파일 생성:
   ```python:requirements_gcpfunction.txt
   startLine: 1
   endLine: 3
   ```
6. 환경 변수 설정:
   ```bash
   NOTION_TOKEN=your_notion_integration_token
   NOTION_DATABASE_ID=your_notion_database_id
   PERPLEXITY_API_KEY=your_perplexity_api_key
   ```

### 2. Cloud Scheduler 설정
1. GCP 콘솔 → Cloud Scheduler 접속
2. "작업 만들기" 클릭
3. 스케줄러 설정:
   - 이름: `ai-tool-analyzer-schedule`
   - 리전: `asia-northeast3`
   - 빈도: `0 0 * * 0` (매주 일요일 자정)
   - 시간대: `Asia/Seoul`
4. 대상 설정:
   - HTTP 메서드: POST
   - URL: [Cloud Functions URL]
   - Auth 헤더: OIDC 토큰
   - 서비스 계정: 새로 생성 또는 기존 계정 선택

### 3. 로그 확인
- GCP 콘솔 → Cloud Logging
- 리소스 선택: Cloud Functions
- 함수 이름: ai-tool-analyzer
- 로그 레벨: Info 이상

### 4. 비용 관리
- Cloud Functions 무료 할당량:
  - 2백만 호출/월
  - 400,000 GB-초의 컴퓨팅 시간
  - 200,000 GHz-초의 CPU 시간
- 주 1회 실행 기준 예상 비용: 무료 (무료 할당량 내)