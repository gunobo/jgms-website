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
```

`backend/.env`에서 최소한 다음 값을 채워주세요 (자세한 설정 방법은 2번 섹션 참고):

- `JWT_SECRET` — `openssl rand -hex 32`로 생성
- `GOOGLE_CLIENT_ID` — 구글 OAuth 클라이언트 ID
- `ADMIN_EMAILS` — 최초 관리자로 등록할 학교 구글 이메일 (콤마로 구분)

`frontend/.env`:

- `VITE_GOOGLE_CLIENT_ID` — `backend/.env`의 `GOOGLE_CLIENT_ID`와 동일한 값

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
   - 생성된 **Client ID**를 `backend/.env`의 `GOOGLE_CLIENT_ID`와 `frontend/.env`의 `VITE_GOOGLE_CLIENT_ID`에 넣기 (Client Secret은 사용하지 않습니다 — ID 토큰 방식이라 필요 없음)

### 2-2. 구글 시트 연동용 서비스 계정 (선택)

설문/과제 결과를 구글 스프레드시트에 자동 기록하려면:

1. Google Cloud Console → **APIs & Services → Library**에서 **Google Sheets API** 활성화
2. **IAM & Admin → Service Accounts → Create Service Account**
3. 생성된 서비스 계정 → **Keys → Add Key → JSON** 다운로드
4. JSON 파일에서 `client_email`, `private_key` 값을 각각 `backend/.env`의 `GOOGLE_SERVICE_ACCOUNT_EMAIL`, `GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY`에 붙여넣기 (private_key는 따옴표로 감싼 채로, `\n`을 그대로 유지)
5. 관리자 화면에서 설문/과제를 만든 뒤 "Google 스프레드시트 연동" 카드에 표시되는 서비스 계정 이메일을 대상 스프레드시트에 **편집자**로 공유하고 연결하면 끝

설정하지 않아도 사이트의 다른 기능은 모두 정상 동작합니다 (시트 연동 카드만 비활성화됩니다).

**스프레드시트는 설문/과제마다 따로 연결합니다.** 각 설문·과제 화면에서 원하는 스프레드시트 URL을 붙여넣으면 그 항목은 그 시트에만 기록되고, 다른 항목과 같은 시트를 공유해도 탭(페이지)이 제목 기준으로 자동 분리되어 데이터가 섞이지 않습니다. 과제는 시트 안에 "OO 평가기준표" / "OO 점수" 두 개의 탭이 만들어집니다.

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

## 4. 서버 실배포 (Docker Compose + Cloudflare Tunnel)

라즈베리파이 등 서버 한 대에 전체 스택을 Docker로 띄우고, Cloudflare Tunnel 컨테이너로 외부에 공개하는 방법입니다. 포트 포워딩이나 고정 IP 없이도 HTTPS 도메인으로 접속할 수 있습니다. 이미 그 서버에서 다른 프로젝트들을 여러 개 돌리고 있다면(`docker ps`로 확인), 아래 5106 포트가 겹치지 않는지 먼저 확인하고 겹치면 `docker-compose.prod.yml`의 `web.ports`와 `.env`의 `PUBLIC_URL` 포트만 바꾸면 됩니다. 백엔드(8000)와 MySQL은 호스트 포트를 전혀 쓰지 않도록(내부 네트워크 전용) 만들어놔서 다른 프로젝트와 충돌할 일이 없습니다.

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
cp .env.prod.example .env
```

- `backend/.env`: 로컬 개발과 동일하게 `JWT_SECRET`, `GOOGLE_CLIENT_ID`, `ADMIN_EMAILS`, (선택) 구글 시트 서비스 계정 값을 채웁니다. `GOOGLE_WORKSPACE_HD`로 학교 도메인 제한을 걸어두는 것을 권장합니다.
- 루트 `.env`: MySQL 비밀번호(`MYSQL_ROOT_PASSWORD`, `MYSQL_PASSWORD`)를 실제 운영용 값으로 바꾸고, `PUBLIC_URL`을 실제 도메인(예: `https://club.example.com`)으로 설정합니다. `CLOUDFLARE_TUNNEL_TOKEN`은 4-4에서 발급받아 채웁니다.
- Google Cloud Console의 OAuth 클라이언트 **Authorized JavaScript origins**에도 이 도메인을 추가해야 로그인이 됩니다.

### 4-3. 빌드 및 실행

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

- 프론트엔드(정적 파일 + `/api` 프록시)가 nginx로 컨테이너 내부 80번 포트, 호스트 **5106번 포트**에 뜹니다.
- 백엔드/MySQL은 호스트 포트를 쓰지 않고 nginx를 통해서만 접근됩니다 (CORS 걱정 없음, 같은 origin으로 통신).
- 상태 확인: `docker compose -f docker-compose.prod.yml ps`, `docker compose -f docker-compose.prod.yml logs -f`

### 4-4. Cloudflare Tunnel로 도메인 연결

`docker-compose.prod.yml`에 이미 `cloudflared` 서비스가 포함되어 있어서, 터널 토큰만 발급받아 `.env`에 넣으면 됩니다 (서버에 `cloudflared`를 따로 설치할 필요 없음).

1. [Cloudflare Zero Trust 대시보드](https://one.dash.cloudflare.com/) → **Networks → Tunnels → Create a tunnel**
2. Connector 타입은 **Cloudflared** 선택, 터널 이름 입력 (예: `jgms-club`)
3. 설치 명령어가 표시되는데, 그 안의 `--token` 뒤 값만 복사해서 루트 `.env`의 `CLOUDFLARE_TUNNEL_TOKEN`에 붙여넣습니다 (명령어 전체를 서버에서 실행할 필요 없음 — 이미 Docker 컨테이너로 떠 있음)
4. 대시보드에서 이어서 **Public Hostname** 탭 → 도메인 입력, Service를 `HTTP` / `web:80`으로 설정 (컨테이너 내부 네트워크 이름이라 `web`이라고 입력하면 됩니다)
5. `.env` 저장 후 재기동:
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```

이제 대시보드에서 설정한 도메인으로 접속하면 서버의 사이트로 연결됩니다. Cloudflare가 HTTPS를 자동으로 처리해주므로 별도 인증서 설정이 필요 없습니다. `cloudflared` 컨테이너 로그는 `docker compose -f docker-compose.prod.yml logs -f cloudflared`로 확인할 수 있습니다.

터널을 쓰지 않는다면 `docker-compose.prod.yml`에서 `cloudflared` 서비스를 지우고, 서버의 5106 포트를 직접 공유기 포트포워딩 등으로 열면 됩니다.

### 4-5. 업데이트 배포

```bash
cd JGMS-Club
git pull
docker compose -f docker-compose.prod.yml up -d --build
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

docker-compose.yml            로컬 개발용
docker-compose.prod.yml       배포용 (nginx + 빌드된 프론트, 내부 전용 백엔드)
```
