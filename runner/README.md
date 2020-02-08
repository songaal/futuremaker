# 여기는 READ-ONLY 샘플공간입니다.

이 디렉토리는 봇을 실행하는 runner 스크립트를 넣는 공간입니다.

거래서 API key와 secret등이 들어있기 때문에, 운영스크립트는 이곳에 커밋하면 위험합니다.

그러므로 실제 환경에서는 자신이 원하는 곳에 runner 디렉토리를 만들어서 별도로 운영하세요.

예) /home/swsong/runner 

futuremaker를 git pull 받은 곳의 경로를 스크립트내에서 수정하세요.

예) sys.path.append("/home/swsong/futuremaker")
 