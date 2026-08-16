#--------------------------------------------------------------------------
# 쿠키 동의 팝업을 닫을 때 시도할 버튼 텍스트 후보 (site마다 문구가 달라서
# 여러 개를 순서대로 시도한다)
# --------------------------------------------------------------------------
COOKIE_CONSENT_BUTTON_TEXTS = [
    "모두 동의", "전체 동의", "전체동의", "동의합니다", "동의", "확인",
    "허용", "모두 허용", "쿠키 허용",
    "Accept all", "Accept All", "I agree", "I Agree", "Accept", "Allow all", "Got it",
]
 
# 상세정보/설명 더보기 버튼 후보 (클릭해야 상세 텍스트가 펼쳐지는 사이트 대응)
DETAIL_EXPAND_BUTTON_TEXTS = [
    "상세정보", "상세보기", "상세 정보", "상품상세", "상품 상세",
    "더보기", "더 보기", "펼치기", "상세스펙", "상세 스펙", "전체보기", "전체 보기",
]
 
# 광고/트래킹 요청을 막을 도메인 키워드 (해당 문자열이 요청 URL에 포함되면 차단)
AD_BLOCK_DOMAIN_KEYWORDS = [
    "doubleclick.net", "googlesyndication.com", "googleadservices.com",
    "adservice.google.com", "google-analytics.com", "googletagmanager.com",
    "criteo.com", "criteo.net", "taboola.com", "outbrain.com",
    "adnxs.com", "amazon-adsystem.com", "moatads.com", "scorecardresearch.com",
    "adform.net", "adroll.com", "pubmatic.com", "rubiconproject.com",
    "media.net", "yieldmo.com", "mgid.com", "tenping.kr", "criteo",
]
# 제외 (네이버, 쿠팡)
EXCLUDE_DOMAINS = [
    "naver.com",
    "coupang.com",
]

# 입력받은 URL
TARGET_URLS = [
    "https://kr.misumi-ec.com/vona2/detail/223012352594/?KWSearch=%EC%84%B8%EC%8B%A0%EB%B2%84%ED%8C%94%EB%A1%9C&searchFlow=results2products&list=PageSearchResult&searchCategorySpec=00&variantType=20260226_pk1_88AovbkGezIbwEO_001",
    "https://smartstore.naver.com/volare73/products/12747389253?nl-ts-pid=jExkOdqX5mhssgJVAxo-092102&NaPm=ct%3Dms8oduve%7Cci%3DER17de9f0f%2D8cb9%2D11f1%2D8a86%2Df69823daf2b3%7Ctr%3Dpla%7Chk%3D20b1d4801dd917853235bddecb4eaecaaaf5137f%7Cnacn%3D68qCBIBdEIn9",
    "https://www.festo.com/kr/ko/a/34411/",
    "https://www.coupang.com/vp/products/8075426128?itemId=22746725406&vendorItemId=95355334252&src=1032001&spec=10305199&addtag=400&ctag=8075426128&lptag=V95355334252&itime=20260715161400&pageType=PRODUCT&pageValue=8075426128&wPcid=17834763995228266688860&wRef=cr.shopping.naver.com&wTime=20260715161400&redirect=landing&mcid=333a0a849fce496da7d0e8ed976a5370&n_keyword=&n_ad_group=&n_ad=&n_rank=&n_keyword_id=&n_media=&n_campaign_type=&n_query=",
]