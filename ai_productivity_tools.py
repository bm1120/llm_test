import os
import logging
from dotenv import load_dotenv
import requests
from notion_client import Client
import time
import re

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# 환경 변수 로드
load_dotenv()
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')

class AIToolAnalyzer:
    def __init__(self):
        self.notion = Client(auth=NOTION_TOKEN)
        self.perplexity_api_key = PERPLEXITY_API_KEY

    def query_perplexity(self, prompt):
        try:
            headers = {
                'Authorization': f'Bearer {self.perplexity_api_key}',
                'Content-Type': 'application/json'
            }
            # 요금 절약을 위해 테스트시에는 llama-3.1-8b-instruct 사용, 모델에 따라 출력이 다를수 있기 때문에 유의
            payload = {
                'model': 'llama-3.1-sonar-small-128k-online',
                'messages': [
                    {
                        'role': 'system',
                        'content': 'AI 도구 분석 전문가입니다. 한국어로 명확하고 구체적인 정보를 제공합니다.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            }

            logging.info("Perplexity API 요청 시작...")
            response = requests.post(
                'https://api.perplexity.ai/chat/completions',
                headers=headers,
                json=payload,
                timeout=20
            )

            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                logging.info("API 요청 성공")
                return content
            else:
                raise Exception(f"API 오류: {response.status_code}")
                
        except Exception as e:
            logging.error(f"API 요청 중 오류: {str(e)}")
            raise

    def get_existing_tools(self):
        """노션 데이터베이스에서 기존 도구 목록 가져오기"""
        try:
            response = self.notion.databases.query(
                database_id=NOTION_DATABASE_ID
            )
            
            existing_tools = set()
            for page in response.get('results', []):
                title = page['properties']['Name']['title']
                if title:
                    tool_name = title[0]['text']['content'].lower()
                    existing_tools.add(tool_name)
            
            logging.info(f"기존 등록된 도구 수: {len(existing_tools)}")
            return existing_tools
            
        except Exception as e:
            logging.error(f"기존 도구 목록 조회 중 오류: {str(e)}")
            return set()

    def get_tool_list(self):
        prompt = """
2024년 3월 기준으로 AI를 활용한 최신 생산성 도구들을 리스트로 작성해주세요.
각 도구는 다음 형식으로 작성해주세요:

1. **도구명** - 주요 기능 설명 (반드시 실제 서비스나 제품 이름이어야 함)
2. **도구명** - 주요 기능 설명
...

예시:
1. **Claude** - AI 문서 분석 및 작성
2. **Copilot Pro** - AI 코드 및 문서 생성

최소 8개, 최대 10개의 도구를 추천해주세요.
일반 명사나 카테고리가 아닌 실제 AI 도구/서비스 이름만 작성해주세요.
"""
        try:
            # 기존 도구 목록 가져오기
            existing_tools = self.get_existing_tools()
            
            response = self.query_perplexity(prompt)
            logging.info("AI 도구 목록 조회 완료")
            logging.info("=== 전체 응답 내용 ===")
            logging.info(response)
            logging.info("===================")
            
            tools = []
            lines = response.split('\n')
            
            # 일반 명사나 카테고리로 의심되는 단어들
            excluded_terms = {'문법', '번역', '분석', '요약', '생성', '검색', '편집', '작성', 
                             'ai', 'tool', 'service', 'platform', 'software'}
            
            for line in lines:
                if line.strip() and '-' in line:
                    match = re.search(r'\*\*(.*?)\*\*', line)
                    if match:
                        tool_name = match.group(1).strip()
                        # 도구명이 제외 목록에 없고, 2글자 이상이며, 영문/숫자가 1개 이상 포함되고,
                        # 기존 도구 목록에 없는 경우만 추가
                        if (tool_name.lower() not in excluded_terms and 
                            len(tool_name) >= 2 and 
                            re.search(r'[a-zA-Z0-9]', tool_name) and
                            tool_name.lower() not in existing_tools):
                            tools.append(tool_name)
            
            if not tools:
                logging.error("새로운 도구가 없습니다.")
                return []
                
            logging.info("=== 추출된 새로운 AI 도구 목록 ===")
            for i, tool in enumerate(tools, 1):
                logging.info(f"{i}. {tool}")
            logging.info(f"총 {len(tools)}개의 새로운 도구가 발견되었습니다.")
            logging.info("======================")
            
            return tools
            
        except Exception as e:
            logging.error(f"도구 목록 조회 중 오류 발생: {str(e)}")
            logging.error("전체 응답:")
            logging.error(response if 'response' in locals() else "응답 없음")
            return []

    def clean_text(self, text):
        """참조 번호, 주석 등을 제거하는 함수"""
        # [숫자] 형식의 참조 번호 제거
        text = re.sub(r'\[\d+\]', '', text)
        # (숫자) 형식의 참조 번호 제거
        text = re.sub(r'\(\d+\)', '', text)
        # 각주 표시 제거
        text = re.sub(r'\[note: .*?\]', '', text)
        # 여러 공백을 하나로 치환
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def analyze_ai_tool(self, tool_name):
        prompt = f"""
{tool_name}에 대해 다음 형식으로 분석해주세요:

### 도구 개요
**출시 정보**
- 출시/업데이트 시점
- 개발사 정보

**주요 특징**
- 핵심 AI 기술
- 차별화 포인트

### 핵심 기능
**AI 기능**
- 주요 AI 기능 3가지
- 기술적 특징

**활용 사례**
- 실제 업무 적용 예시
- 생산성 향상 효과

### 가격 정책
**무료 제공**
- 기본 기능 범위
- 사용 제한

**유료 플랜**
- 요금제 구성
- 기업용 옵션

### 확장성
**연동 옵션**
- API 제공
- 주요 통합 서비스

### 평가
**장점**
- 핵심 강점
- 경쟁력

**개선 필요**
- 현재 한계점
- 향후 과제

마지막 줄에는 공식 웹사이트 URL만 입력해주세요.
"""
        try:
            analysis = self.query_perplexity(prompt)
            if analysis:
                # URL 추출 전에 텍스트 정제
                lines = analysis.split('\n')
                url_line = None
                cleaned_lines = []
                
                for line in lines:
                    # URL이 포함된 줄 찾기
                    if 'http' in line.lower():
                        url_line = line
                        continue
                    # 'URL' 또는 '공식' 또는 '웹사이트'가 포함된 제목줄 건너뛰기
                    if any(keyword in line.lower() for keyword in ['url', '식', '웹사이트']):
                        continue
                    # 빈 줄이 아닌 경우에만 정제
                    if line.strip():
                        cleaned_line = self.clean_text(line)
                        if cleaned_line:  # 정제 후에도 내용이 있는 경우만 추가
                            cleaned_lines.append(cleaned_line)
                
                # 정제된 분석 내용
                cleaned_analysis = '\n'.join(cleaned_lines)
                
                logging.info(f"{tool_name} 분석 완료, Notion에 저장 시도 중...")
                self.add_to_notion(tool_name, cleaned_analysis, url_line)
                return True
            return False
        except Exception as e:
            logging.error(f"{tool_name} 분석 중 오류: {str(e)}")
            return False

    def add_to_notion(self, tool_name, analysis, url=None):
        try:
            clean_tool_name = tool_name.replace('**', '').strip()
            logging.info(f"Notion 페이지 생성 시작: {clean_tool_name}")
            
            # URL 정제
            if url:
                website_url = re.search(r'https?://[^\s\[\]()]*', url)
                website_url = website_url.group(0).strip() if website_url else None
                website_url = re.sub(r'[.,;:]$', '', website_url) if website_url else None
            else:
                website_url = None
            
            # 페이지 생성
            page = self.notion.pages.create(
                parent={"database_id": NOTION_DATABASE_ID},
                properties={
                    "Name": {"title": [{"text": {"content": clean_tool_name}}]},
                    "Link": {"url": website_url} if website_url else {"url": None}
                }
            )
            
            blocks = []
            
            # 메인 제목
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": f"{clean_tool_name} 분석 리포트"}}]
                }
            })
            
            def clean_content(text):
                # **키워드**: 값 형식 처리
                if '**' in text and '**: ' in text:
                    parts = text.split('**: ')
                    if len(parts) == 2:
                        keyword = parts[0].replace('**', '')
                        return f"{keyword}: {parts[1]}"
                
                # **키워드** 값 형식 처리
                if text.count('**') == 2:
                    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
                
                return text

            current_text = []
            for line in analysis.split('\n'):
                stripped_line = line.strip()
                
                # 모든 라인에 대해 ** 패턴 정리
                stripped_line = clean_content(stripped_line)
                
                if stripped_line.startswith('###'):  # 대제목 (heading_2)
                    if current_text:
                        blocks.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"type": "text", "text": {"content": '\n'.join(current_text)}}]
                            }
                        })
                        current_text = []
                    
                    blocks.append({
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": stripped_line.replace('### ', '')}}]
                        }
                    })
                elif stripped_line.startswith('-'):  # 목록 항목
                    if current_text and not current_text[-1].startswith('-'):
                        blocks.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"type": "text", "text": {"content": '\n'.join(current_text)}}]
                            }
                        })
                        current_text = []
                    
                    content = stripped_line.replace('- ', '')
                    blocks.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{"type": "text", "text": {"content": content}}]
                        }
                    })
                else:
                    current_text.append(stripped_line)
            
            if current_text:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": '\n'.join(current_text)}}]
                    }
                })
            
            # 블록 추가
            self.notion.blocks.children.append(
                page["id"],
                children=blocks
            )
            
            logging.info(f"Notion 페이지 생성 완료: {page['url']}")
            return True
            
        except Exception as e:
            logging.error(f"Notion 추가 중 오류: {str(e)}")
            return False

def create_text_blocks(text):
    """텍스트를 Notion 블록으로 변환"""
    blocks = []
    if text.strip():
        # 일반 텍스트를 단락으로 처리
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text.strip()}}]
            }
        })
    return blocks

def main():
    analyzer = AIToolAnalyzer()
    
    try:
        # AI 도구 목록 가져오기
        tools = analyzer.get_tool_list()
        
        if not tools:
            logging.error("도구 목록이 비어있어 분석을 행할 수 없습니다.")
            return
            
        logging.info(f"총 {len(tools)}개의 도구를 분석합니다.")
        
        success_count = 0
        for i, tool in enumerate(tools, 1):
            try:
                logging.info(f"=== {i}/{len(tools)} : {tool} 분석 시작 ===")
                if analyzer.analyze_ai_tool(tool):
                    success_count += 1
                    logging.info(f"{tool} 분석 및 저장 완료 ({success_count}/{len(tools)})")
                else:
                    logging.error(f"{tool} 분석 실패")
                    continue
                
                time.sleep(3)  # API 요청 간격
                
            except Exception as e:
                logging.error(f"{tool} 처리 중 오류 발생: {str(e)}")
                continue
                
        logging.info(f"분석 완료: 총 {len(tools)}개 중 {success_count}개 성공")
            
    except Exception as e:
        logging.error(f"실행 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    main() 