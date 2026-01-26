# mega-project

1. 충돌 방지를 위해 가상환경을 만들어주세요.
파이썬에서 가상 환경을 생성하고 관리하기 위한 모듈 'venv'
   
# 가상 환경을 생성하는 코드
python -m venv myenv

이때 myenv는 가상환경 이름으로, 마음대로 가상환경 이름을 만들 수 있습니다. 

# 가상 환경을 활성화하는 코드 (Windows)
myenv\Scripts\activate

# 가상 환경을 활성화하는 코드 (macOS, Linux)
source myenv/bin/activate

# 가상 환경을 비활성화하는 코드
deactivate

참고: https://wikidocs.net/237667

2. 프로젝트의 주요 의존성 패키지를 설치해주세요. (가상환경 활성화 후, 설치를 진행해주세요.)

# 의존성 패키지 설치 코드
pip install -r requirements.txt

3. ../hr_project 경로 안에서 다음 명령어를 실행주세요.

# 로컬 서버 실행 코드 
python manage.py runserver

4. 웹 이동
Starting development server at http://(설정된 ip 주소)/
위와 같이 뜨면 ctrl + 마우스 클릭을 통해 웹으로 이동할 수 있습니다. 
