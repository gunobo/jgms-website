# 창의적 소프트웨어 체험·활용반 동아리 사이트

학교 구글 계정으로 로그인하는 동아리 사이트입니다.

- **관리자**: 학생 명단 관리, 설문조사(구글 폼 스타일) 생성/응답 조회, 과제 + 평가기준표(루브릭) 생성 및 체크박스 채점
- **학생**: 학교 구글 계정으로 로그인, 설문 응답, 과제 제출(링크/텍스트/파일), 채점 결과 확인
- **구글 시트 연동**: 설문 응답과 과제 채점 결과(+ 평가기준표)를 지정한 구글 스프레드시트에 실시간으로 기록

## 기술 스택

- 프론트엔드: React 19 + TypeScript + Vite + Tailwind CSS
- 백엔드: FastAPI (Python) + SQLAlchemy + Alembic
- DB: MySQL 8.4
- 인증: 구글 로그인(OAuth ID 토큰) → 자체 JWT 발급
- 배포: Docker / Docker Compose

---

## 1. 로컬 개발 환경 (Docker Compose)

### 준비물

- Docker Desktop (또는 Docker Engine + Compose plugin)

### 환경변수 파일 만들기

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
cp .env.example .env
```

`backend/.env`에서 최소한 다음 값을 채워주세요 (자세한 설정 방법은 2번 섹션 참고):

- `JWT_SECRET` — `openssl rand -hex 32`로 생성
- `GOOGLE_CLIENT_ID` — 구글 OAuth 클라이언트 ID
- `ADMIN_EMAILS` — 최초 관리자로 등록할 학교 구글 이메일 (콤마로 구분)

루트 `.env`의 `VITE_GOOGLE_CLIENT_ID` — 위 `GOOGLE_CLIENT_ID`와 동일한 값. 프론트가 빌드 시점에 이 값을 JS에 박아 넣기 때문에 **`frontend/.env`가 아니라 루트 `.env`** 에 넣어야 실제로 반영됩니다 (`frontend/.env`는 Docker 없이 직접 `npm run dev`로 띄울 때만 쓰임).

### 실행

```bash
docker compose up -d --build
```

첫 실행 시 자동으로 DB 마이그레이션이 적용됩니다. 완료되면:

- 프론트엔드: http://localhost:5174
- 백엔드 API 문서: http://localhost:8001/docs

> 포트가 5173/8000이 아닌 5174/8001인 이유: 로컬에 다른 프로젝트(RE:ACT)가 그 포트를 이미 쓰고 있어서 충돌을 피하려고 바꿨습니다. 다른 환경에서는 `docker-compose.yml`의 포트 매핑을 원하는 대로 바꿔도 됩니다.

### 로그 / 중지

```bash
docker compose logs -f backend
docker compose down          # 컨테이너 중지 (데이터는 volume에 보존됨)
docker compose down -v       # 데이터까지 완전 삭제
```

---

## 2. 구글 클라우드 설정

로그인과 구글 시트 연동을 위해 두 가지를 만들어야 합니다.

### 2-1. 로그인용 OAuth 클라이언트 (필수)

1. [Google Cloud Console](https://console.cloud.google.com/) → 새 프로젝트 생성 (또는 기존 프로젝트 사용)
2. **APIs & Services → OAuth consent screen**에서 동의 화면 설정
   - 학교 Google Workspace 계정만 로그인하게 하려면 User type을 **Internal**로, 또는 External로 두고 `backend/.env`의 `GOOGLE_WORKSPACE_HD`에 학교 도메인(예: `jgms.hs.kr`)을 입력하세요.
3. **APIs & Services → Credentials → Create Credentials → OAuth client ID**
   - Application type: **Web application**
   - Authorized JavaScript origins에 사이트 주소 추가 (로컬 개발: `http://localhost:5174`, 배포 시: 실제 도메인)
   - 생성된 **Client ID**를 `backend/.env`의 `GOOGLE_CLIENT_ID`와 루트 `.env`의 `VITE_GOOGLE_CLIENT_ID`에 넣기 (Client Secret은 사용하지 않습니다 — ID 토큰 방식이라 필요 없음)
   - OAuth consent screen이 "테스트" 상태면 등록한 테스트 사용자만 로그인 가능합니다. 여러 명이 로그인해야 하면 **PUBLISH APP**으로 게시하세요 (민감하지 않은 스코프만 써서 별도 심사 없이 바로 게시됩니다).

### 2-2. 구글 시트 연동용 서비스 계정 (선택)

설문/과제/학생 명단을 구글 스프레드시트에 자동 기록하려면:

1. Google Cloud Console → **APIs & Services → Library**에서 **Google Sheets API**와 **Google Drive API** 둘 다 활성화 (Drive API는 과제 채점표를 자동으로 만들고 관리자에게 공유해주는 데 필요)
2. **IAM & Admin → Service Accounts → Create Service Account**
3. 생성된 서비스 계정 → **Keys → Add Key → JSON** 다운로드
4. JSON 파일에서 `client_email`, `private_key` 값을 각각 `backend/.env`의 `GOOGLE_SERVICE_ACCOUNT_EMAIL`, `GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY`에 붙여넣기 (private_key는 따옴표로 감싼 채로, `\n`을 그대로 유지)

설정하지 않아도 사이트의 다른 기능은 모두 정상 동작합니다 (시트 연동 카드만 비활성화됩니다).

**설문 / 학생 명단**: 관리자 화면에서 "Google 스프레드시트 연동" 카드에 표시되는 서비스 계정 이메일을 대상 스프레드시트에 **편집자**로 공유한 뒤 URL을 붙여넣으면 연결됩니다. 학생 명단은 명단이 바뀔 때마다(추가/삭제) 연결된 시트가 자동으로 다시 갱신됩니다.

**과제**: 새 과제를 만들면 채점표용 스프레드시트가 **자동으로 만들어지고, 만든 관리자 계정에 자동 공유**됩니다 (별도로 시트를 만들고 연결할 필요 없음). 필요하면 과제의 "제출물 / 채점" 화면에서 다른 시트로 다시 연결할 수도 있습니다.

**스프레드시트는 항목마다 따로/같이 쓸 수 있습니다.** 여러 설문·과제에 같은 스프레드시트 URL을 연결해도 탭(페이지)이 제목 기준으로 자동 분리되어 데이터가 섞이지 않고, 다른 URL을 쓰면 완전히 별개의 파일로 나뉩니다. 과제는 시트 안에 "OO 평가기준표" / "OO 점수" 두 개의 탭이 만들어집니다.

---

## 3. GitHub에 올리기

```bash
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

`.env` 파일들은 `.gitignore`에 의해 자동으로 제외됩니다 (`.env.example`만 커밋됨). 비밀번호/키를 실수로 커밋하지 않았는지 `git status`로 한 번 확인하세요.

---

## 4. 서버 배포 (같은 docker-compose.yml + Cloudflare Tunnel)

로컬 개발과 실제 서버 배포에 **같은 `docker-compose.yml`을 그대로** 씁니다. 별도의 "배포용" 파일은 없습니다. 서버 한 대(라즈베리파이 등)에서 컨테이너를 그대로 띄우고, `cloudflared` 컨테이너 하나가 Cloudflare Tunnel로 외부에 공개해줍니다. 포트 포워딩이나 고정 IP, nginx, 인증서 설정이 전혀 필요 없습니다.

프론트엔드(5174)와 백엔드(8001, 3306)가 쓰는 호스트 포트는 이미 그 서버에서 돌아가는 다른 프로젝트들(`docker ps`로 확인)과 겹치지 않는 걸 확인했습니다.

### 4-1. 서버에 Docker 설치

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# 이후 재로그인 (또는 재부팅) 필요
```

### 4-2. 저장소 클론 및 설정

```bash
git clone <your-github-repo-url>
cd JGMS-Club

cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
cp .env.example .env
```

- `backend/.env`: 로컬 개발과 동일하게 `JWT_SECRET`, `GOOGLE_CLIENT_ID`, `ADMIN_EMAILS`, (선택) 구글 시트 서비스 계정 값을 채웁니다. `GOOGLE_WORKSPACE_HD`로 학교 도메인 제한을 걸어두는 것을 권장합니다.
- `frontend/.env`: 안 건드려도 됩니다 (아래 루트 `.env`가 빌드 시점에 덮어씀).
- 루트 `.env`: MySQL 비밀번호(`MYSQL_ROOT_PASSWORD`, `MYSQL_PASSWORD`)를 실제 값으로 바꾸고, `VITE_GOOGLE_CLIENT_ID`에 `GOOGLE_CLIENT_ID`와 같은 값을 넣습니다. `FRONTEND_ORIGIN`/`VITE_API_URL`은 기본값(`https://jgms.imjemin.co.kr`, `https://jgms-api.imjemin.co.kr`)을 그대로 쓰면 됩니다. `CLOUDFLARE_TUNNEL_TOKEN`은 4-4에서 발급받아 채웁니다.
- Google Cloud Console의 OAuth 클라이언트 **Authorized JavaScript origins**에 `https://jgms.imjemin.co.kr`을 추가해야 로그인이 됩니다.

### 4-3. 빌드 및 실행

```bash
docker compose up -d --build
```

로컬 개발 때와 완전히 같은 명령어입니다. 상태 확인: `docker compose ps`, `docker compose logs -f`

### 4-4. Cloudflare Tunnel로 도메인 연결

프론트엔드와 백엔드를 각각 서브도메인으로 나눠서 연결합니다 (nginx 프록시 없이 Cloudflare가 라우팅을 대신 해줌).

1. [Cloudflare Zero Trust 대시보드](https://one.dash.cloudflare.com/) → **Networks → Tunnels → Create a tunnel**
2. Connector 타입은 **Cloudflared** 선택, 터널 이름 입력 (예: `jgms-club`)
3. 설치 명령어가 표시되는데, 그 안의 `--token` 뒤 값만 복사해서 루트 `.env`의 `CLOUDFLARE_TUNNEL_TOKEN`에 붙여넣습니다 (명령어 전체를 서버에서 실행할 필요 없음 — 아래처럼 이미 Docker 컨테이너로 뜸)
4. 대시보드에서 이어서 **Public Hostname** 탭에 두 개를 등록:
   - `jgms.imjemin.co.kr` → Service `HTTP` / `frontend:5173`
   - `jgms-api.imjemin.co.kr` → Service `HTTP` / `backend:8000`
   (`frontend`/`backend`는 컨테이너 내부 네트워크 이름이라 그대로 입력하면 됩니다)
5. `cloudflared`는 기본적으로 꺼져 있는 서비스라 `--profile tunnel`을 붙여서 실행합니다:
   ```bash
   docker compose --profile tunnel up -d
   ```

이제 `https://jgms.imjemin.co.kr`로 접속하면 서버의 사이트로 연결됩니다. Cloudflare가 HTTPS를 자동으로 처리해주므로 별도 인증서 설정이 필요 없습니다. `cloudflared` 로그는 `docker compose logs -f cloudflared`로 확인할 수 있습니다.

### 4-5. 업데이트 배포

```bash
cd JGMS-Club
git pull
docker compose --profile tunnel up -d --build
```

DB 마이그레이션은 backend 컨테이너 시작 시 자동으로 적용됩니다.

### 4-6. 백업

MySQL 데이터와 과제 첨부파일은 각각 `mysql_data`, `backend_uploads`라는 Docker volume에 저장됩니다.

```bash
docker run --rm -v jgms-club_mysql_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/mysql_data_backup.tar.gz -C /data .
```

---

## 프로젝트 구조

```
backend/              FastAPI 백엔드
  app/
    models.py          SQLAlchemy 모델
    schemas.py          Pydantic 스키마
    routers/            API 라우터
    sheets.py            구글 시트 연동
  alembic/              DB 마이그레이션

frontend/              React (Vite) 프론트엔드
  src/
    pages/admin/         관리자 화면
    pages/student/        학생 화면
    api/                  API 클라이언트

docker-compose.yml     로컬 개발 + 서버 배포 공용 (cloudflared는 --profile tunnel 로만 켜짐)
```
