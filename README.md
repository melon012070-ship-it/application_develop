# Android Google Maps Current Location App

Google Maps SDK와 Android 위치 서비스를 활용하여 사용자의 현재 위치를 지도에 표시하는 Android 애플리케이션입니다.

앱 실행 시 위치 권한을 확인하고, 권한이 허용되면 현재 위치를 조회하여 지도 카메라를 이동하고 마커를 표시합니다.

## 주요 기능

- Google 지도 화면 표시
- 앱 실행 중 위치 권한 요청 및 결과 처리
- GPS 기반 현재 위치 조회
- 현재 위치에 마커 표시
- 현재 위치로 지도 카메라 자동 이동
- 위치 정보를 가져오지 못했을 때 기본 위치 표시
- 지도 확대·축소 컨트롤 제공

## 사용 기술

- Kotlin
- Android Studio
- Google Maps SDK for Android
- Google Play services Location API
- FusedLocationProviderClient
- Activity Result API
- Gradle Kotlin DSL

## 동작 과정

1. `SupportMapFragment`를 통해 Google 지도를 불러옵니다.
2. 지도가 준비되면 위치 권한이 허용되었는지 확인합니다.
3. 권한이 없다면 사용자에게 위치 권한을 요청합니다.
4. 권한이 허용되면 `FusedLocationProviderClient`로 최근 위치를 조회합니다.
5. 조회된 위치에 마커를 표시하고 지도 카메라를 이동합니다.
6. 위치를 가져오지 못한 경우 설정된 기본 위치를 표시합니다.

## 프로젝트 구조

```text
.
├── app/
│   ├── build.gradle.kts
│   └── src/main/
│       ├── AndroidManifest.xml
│       ├── java/com/example/myapplication19/
│       │   └── MainActivity.kt
│       └── res/
│           ├── layout/activity_main.xml
│           ├── values/
│           └── xml/
├── gradle/
│   ├── libs.versions.toml
│   └── wrapper/
├── build.gradle.kts
├── settings.gradle.kts
└── gradle.properties
```

## 실행 준비

1. Google Cloud Console에서 프로젝트를 생성합니다.
2. `Maps SDK for Android`를 활성화합니다.
3. Android 앱용 API 키를 생성합니다.
4. API 키에 패키지 이름과 SHA-1 인증서 지문 제한을 설정합니다.
5. 로컬 환경에 API 키를 설정한 후 Android Studio에서 프로젝트를 실행합니다.

> 실제 Google Maps API 키는 저장소에 포함하지 않습니다. API 키, `local.properties`, 서명 키와 로컬 로그는 `.gitignore`로 제외해야 합니다.

## 권한

현재 위치 표시를 위해 다음 권한을 사용합니다.

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
```

스크린샷에는 API 키, Google 계정, 실제 거주지 등 민감한 정보가 포함되지 않도록 주의해야 합니다.

## 개선 방향

- 최신 위치를 직접 요청하는 로직 추가
- 위치 권한 거부 시 안내 메시지 제공
- GPS 비활성화 상태 처리
- 로딩 및 오류 상태 UI 추가
- 테스트 코드 작성

## 보안 안내

- Google Maps API 키를 소스코드나 문서에 직접 작성하지 않습니다.
- API 키는 Android 앱의 패키지 이름과 SHA-1 인증서로 제한합니다.
- 키가 노출된 경우 저장소에서 파일만 삭제하지 않고 Google Cloud Console에서 즉시 폐기 또는 재발급합니다.

